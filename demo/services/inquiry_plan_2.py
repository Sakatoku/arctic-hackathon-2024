import json
import re
from getpass import getpass
from typing import Dict, Tuple

import pandas as pd
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.functions import call_udf, col, flatten, lit, not_, concat
from snowflake.snowpark.types import StructType, StructField, StringType, IntegerType

## pip install snowflake-snowpark-python pandas

def get_session() -> Session:
    try:
        connection_parameters = json.loads(open('./secrets/snowflake_connection.json').read())
    except:
        connection_parameters = {
            "account": input("input accountname: "),
            "user": input("input username: "),
            "password": getpass("input password: "),
            "role": "SYSADMIN",  # optional
            "warehouse": "COMPUTE_WH",  # optional
            "database": "TOURISM",  # optional
            "schema": "PUBLIC",  # optional
        }  

    session = Session.builder.configs(connection_parameters).create()

    return session

def get_dummy_request() -> str:
    request = '''
    {
    "destination":"san-francisco"
    "purpose":"観光"
    "traveler":{
    "age":"20"
    "number_of_people":"4"
    }
    "travel_dates":{
    "start_date":"2023-06-03"
    "end_date":"2023-06-04"
    }
    "budget":"30万円"
    "food_preferences":"シーフードと中華料理"
    "activity_preferences":"海に入りたい"
    "notes":""
    }
    '''

    return request


def convert_json_text(input: str) -> str:
    json_pattern = r'\{[\s\S]*?\}'
    match = re.search(json_pattern, input)

    if match:
        json_str = match.group(0)
        try:
            data = json.loads(json_str)  # JSON文字列をPythonの辞書に変換
            return data
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            return None
    else:
        print("No JSON data found")
        return None
    

def get_restaurants_list(session: Session, request: str):
    df = session.table("tourism.public.cl_restaurants_finalized")
    categories = df.select_expr("LISTAGG(DISTINCT cuisine, ' , ')").collect()[0][0]
    print(categories)
    output_format = '{"MM/DD hh:mm": "category1", "MM/DD hh:mm": "category2"}'
    response = df.select(call_udf("snowflake.cortex.complete", 
                            lit('snowflake-arctic'),
                            lit('顧客属性<customer_requests>をもとに、レストランカテゴリ<categories>のリストの中から日数分×朝(8時)・昼(12時)・晩(18時)分のカテゴリを選択して、出力形式<output_format>に則ってJSONを出力しなさい。文章ではなく、<output_format>に則った返答をすることに必ず則ってください。\\n'
                                f'<customer_requests>{request}</customer_requests>\\n<categories>{categories}</categories>\\n<output_format>{output_format}</output_format>')
                            ).alias('response')).limit(1).to_pandas()["RESPONSE"].iloc[0]

    converted_response = convert_json_text(response)
    return converted_response


def get_tour_spots(session: Session, request: str):
    df = session.table("tourism.public.tourism_spots_finalized")
    categories = df.select_expr("LISTAGG(DISTINCT category, ' , ')").collect()[0][0]
    print(categories)
    output_format = '{"MM/DD hh:mm": "tour category name", "MM/DD hh:mm": "tour category name", …}'
    response = df.select(call_udf("snowflake.cortex.complete", 
                            lit('snowflake-arctic'), 
                            lit('顧客属性<request>をもとに、観光地<category>をどの時間帯に訪れるべきか考えて（食事の時間帯(8時,12時,18時)を避ける）、出力形式<output_sample>で出力しなさい。'
                                'このとき、文章を出力してはいけません。出力形式のみを出力しなさい。\\n'
                                f'<request>{request}</request>\\n<category>{categories}</category>\\n<output_sample>{output_format}</output_sample>')
                            ).alias('response')).limit(1).to_pandas()["RESPONSE"].iloc[0]

    converted_response = convert_json_text(response)
    return converted_response


def extract_record(session: Session, table_name: str, category_col_name: str, spots: Dict[str, str], request_description: str) -> pd.DataFrame:
    result_df = []
    selected_names = set()
    
    df_base = session.table(table_name)
    df_base = df_base.with_column("costomer_pref_v", call_udf("snowflake.cortex.EMBED_TEXT_768", lit('snowflake-arctic-embed-m'), lit(request_description)))
    df_base = df_base.with_column("cos_sim", call_udf("VECTOR_COSINE_SIMILARITY", col("costomer_pref_v"), col("embeded_web_summary")))
    df_base = df_base.with_column("score", col("cos_sim")+(1-(col("sum_crime")-1291)/(68930-1291))*0.05)
    df_base.write.mode("overwrite").save_as_table("tourism.public.temp_table", table_type="temporary")
    for spot_k, spot_v in spots.items():
        df = session.table("tourism.public.temp_table")
        df = df.where(col(category_col_name)==spot_v)
        if selected_names:
            df = df.where(not_(col("name").in_(selected_names)))
        if df.count() == 0:
            continue
        # df = df.with_column("costomer_pref_v", call_udf("snowflake.cortex.EMBED_TEXT_768", lit('snowflake-arctic-embed-m'), lit(request_description)))
        #df = df.with_column("web_summary_v", call_udf("snowflake.cortex.EMBED_TEXT_768", lit('snowflake-arctic-embed-m'), col("web_summary")))
        df = df.sort(col("score").desc()).limit(1)
        df = df.with_column("visit_time", lit(spot_k))
        df.collect()
        
        pd_df = df.to_pandas()
        selected_names.add(pd_df["NAME"][0])
        result_df.append(pd_df)
        
    return pd.concat(result_df, ignore_index=True).sort_values(by=["VISIT_TIME"], ascending=[True])

# 文字列をエスケープする: SQL用
def escape_string_for_sql(s):
    return s.replace("'", "''")

def get_requested_df(session: Session, request: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    total_steps = 4
    progress_bar = st.progress(0, text="Extracting in progress using llm and your preferences. Please wait.")
    for _ in range(3):
        restaurants_list = get_restaurants_list(session, request)
        progress_bar.progress(1.0 / total_steps)
        tour_spots = get_tour_spots(session, request)
        progress_bar.progress(2.0 / total_steps)
        if restaurants_list is not None and tour_spots is not None:
            break

    request_description = session.sql(f"select snowflake.cortex.complete('snowflake-arctic', 'Please describe in sentences the customer attributes especially for activities and food preferences in English based on the following JSON request:{request}') as response").to_pandas()["RESPONSE"].iloc[0]
    print(request_description)

    restaurants_result_df = extract_record(session, "tourism.public.cl_restaurants_finalized", "CUISINE", restaurants_list, request_description)
    progress_bar.progress(3.0 / total_steps)
    tour_result_df = extract_record(session, "tourism.public.tourism_spots_finalized", "CATEGORY", tour_spots, request_description)
    progress_bar.progress(4.0 / total_steps)

    print(restaurants_result_df)
    print(tour_result_df)

    restaurants_result_df.to_csv("./log/restaurants_result_df.csv")
    tour_result_df.to_csv("./log/tour_result_df.csv")

    return restaurants_result_df, tour_result_df

if __name__ == "__main__":
    session = get_session()
    request = get_dummy_request()
    get_requested_df(session, request)
