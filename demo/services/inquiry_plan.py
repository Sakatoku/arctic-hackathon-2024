import json
import re
from getpass import getpass
from typing import Dict, Tuple

import pandas as pd
import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark
from snowflake.snowpark import Session
from snowflake.snowpark.functions import call_udf, col, flatten, lit, not_, concat

@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflakeに接続する
    # Snowflakeの接続情報はStreamlitのシークレット(.streamlit/secret.toml)に保存しておく
    connection = snowflake.connector.connect(
        user=st.secrets["Snowflake"]["user"],
        password=st.secrets["Snowflake"]["password"],
        account=st.secrets["Snowflake"]["account"],
        role=st.secrets["Snowflake"]["role"],
        warehouse=st.secrets["Snowflake"]["warehouse"])

    # Snowparkセッションを作成する
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

def get_dummy_request() -> str:
    request = '''
        サンフランシスコに友達4人（30代）と観光に行きます。
        特に、絶景や公園でゆったりや、サンフランシスコの名所に行きたいです。
        また、日本料理やサンフランシスコ料理を食べたいです。

        予算は100万円で、旅程は6/2から6/4です。
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
    df_base = df_base.with_column("customer_pref_v", call_udf("snowflake.cortex.EMBED_TEXT_768", lit('snowflake-arctic-embed-m'), lit(request_description)))
    df_base = df_base.with_column("cos_sim", call_udf("VECTOR_COSINE_SIMILARITY", col("customer_pref_v"), col("embeded_web_summary")))
    try:
        df_base = df_base.with_column("score", col("cos_sim")+(1-(col("sum_crime")-1291)/(68930-1291))*0.05)
        df_base.write.mode("overwrite").save_as_table("tourism.public.temp_table", table_type="temporary")
    except:
        df_base = df_base.with_column("score", col("cos_sim"))
        df_base.write.mode("overwrite").save_as_table("tourism.public.temp_table", table_type="temporary")
    
    for spot_k, spot_v in spots.items():
        df = session.table("tourism.public.temp_table")
        df = df.where(col(category_col_name)==spot_v)
        if selected_names:
            df = df.where(not_(col("name").in_(selected_names)))
        if df.count() == 0:
            continue

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

def get_arctic_request(session: Session, request: str) -> str:
    return session.sql(f"select snowflake.cortex.complete('snowflake-arctic', 'Please describe in sentences the customer attributes especially for activities and food preferences in English based on the following JSON request:{request}') as response").to_pandas()["RESPONSE"].iloc[0]

def get_requested_df(session: Session, request: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    request = get_arctic_request(session, request)
    with st.expander("Your request understood by Arctic."):
        try:
            st.write(request)
        except:
            st.write("sorry, we can't display your request. but we can proceed.")

    request = escape_string_for_sql(request)
    total_steps = 4
    progress_bar = st.progress(0, text="Extracting in progress using llm and your preferences. Please wait.")
    for _ in range(3):
        restaurants_list = get_restaurants_list(session, request)
        progress_bar.progress(1.0 / total_steps)
        tour_spots = get_tour_spots(session, request)
        progress_bar.progress(2.0 / total_steps)
        if restaurants_list is not None and tour_spots is not None:
            break

    restaurants_result_df = extract_record(session, "tourism.public.cl_restaurants_finalized", "CUISINE", restaurants_list, request)
    progress_bar.progress(3.0 / total_steps)
    tour_result_df = extract_record(session, "tourism.public.tourism_spots_finalized", "CATEGORY", tour_spots, request)
    progress_bar.progress(4.0 / total_steps)

    print(restaurants_result_df)
    print(tour_result_df)

    # 生成したアクティビティの情報を表示する
    with st.expander("Found Activities"):
        st.write("Here is your restraurants.")
        st.dataframe(restaurants_result_df)
        st.write("Here is your tourism spot.")
        st.dataframe(tour_result_df)

    restaurants_result_df.to_csv("./log/restaurants_result_df.csv")
    tour_result_df.to_csv("./log/tour_result_df.csv")

    return restaurants_result_df, tour_result_df

if __name__ == "__main__":
    session = connect_snowflake()
    request = get_dummy_request()
    get_requested_df(session, request)
