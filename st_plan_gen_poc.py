import streamlit as st
import pandas as pd

# Snowflake and Snowpark
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex

import json
import datetime
import replicate
import os

# 接続するSnowflake環境を指定する
ENVIRONMENT = "SnowflakeProd"

# ReplicateのAPIキーを環境変数に設定する
os.environ["REPLICATE_API_TOKEN"] = st.secrets["Replicate"]["apikey"]

# ローカルPython環境からSnowflakeに接続するための関数
@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflakeに接続する
    # Snowflakeの接続情報はStreamlitのシークレット(.streamlit/secret.toml)に保存しておく
    connection = snowflake.connector.connect(
        user=st.secrets[ENVIRONMENT]["user"],
        password=st.secrets[ENVIRONMENT]["password"],
        account=st.secrets[ENVIRONMENT]["account"],
        role=st.secrets[ENVIRONMENT]["role"],
        warehouse=st.secrets[ENVIRONMENT]["warehouse"])

    # Snowparkセッションを作成する
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

# 文字列をエスケープする: SQL用
def escape_string_for_sql(s):
    return s.replace("'", "''")

# 文字列をエスケープする: JSON用
def escape_string_for_json(s):
    return s.replace('"', '\\"')

# Snowflakeからレストランデータを取得する
def get_restaurant_data_from_snowflake(name, cuisine):
    # Snowflakeに接続する
    session = connect_snowflake()
    # SQLを実行してデータを取得する
    df_sql = session.sql("SELECT * FROM TOURISM.PUBLIC.CL_RESTAURANTS_FINALIZED WHERE NAME = '{}' AND CUISINE = '{}' LIMIT 1".format(escape_string(name), escape_string(cuisine))).to_pandas()
    return df_sql

# キャッチフレーズと詳細な説明を生成する
def generate_description(data, visit_time):
    name = data['NAME'][0]
    cuisine = data['CUISINE'][0]
    summary = data['WEB_SUMMARY'][0]
    prompt = f'Generate a catchphrase and detailed description for this restaurant. Restaurant information is follows: {{ "name": "{name}", "cuisine": "{cuisine}", "visit_time": "{visit_time}", "web_summary": "{summary}" }} Your output should be formatted as follows: {{ "catchphrase": "...", "description": "..." }}'
    prompt = escape_string(prompt)

    # Snowflake Coretex APIを呼び出してテキストを生成する
    session = connect_snowflake()
    selected_model = "snowflake-arctic"
    cmd = f"select snowflake.cortex.complete('{selected_model}', [{{'role': 'user', 'content': '{prompt}'}}], {{'temperature': 0.3}}) as RESPONSE"
    df_response = session.sql(cmd).collect()
    json_response = json.loads(df_response[0]["RESPONSE"])
    return json_response['choices'][0]['messages']

# 日時文字列を正規化する
def detetime_str_normalization(datetime_str: str):
    # 1/1 09:00 -> 2022-01-01T12:00:00Z
    # datetimeでパースしてから、UTCに変換する
    dt = datetime.datetime.strptime(datetime_str, '%m/%d %H:%M')
    dt = dt.replace(year=2024)
    dt = dt.astimezone(datetime.timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# Replicate APIを呼び出して画像を生成する
def generate_image_replicate(user_prompt):
    input = {
        "prompt": user_prompt
    }

    client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])
    output = client.run(
        "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
        input=input
    )
    return output[0]

filename = 'temp/restaurants_result_df.csv'
df = pd.read_csv(filename)
df

# データ生成の進捗表示
generation_progress = st.progress(0.0)

# dfに行先リストが格納されている。1行づつ処理していく
result = []
for index, row in df.iterrows():
    # name, cuisine, visit_timeを取得する
    name = row['NAME']
    cuisine = row['CUISINE']
    visit_time = row['VISIT_TIME']

    # Snowflakeからレストランデータを取得する
    restaurant_data = get_restaurant_data_from_snowflake(name, cuisine)

    # レストランデータからキャッチフレーズと詳細な説明を生成する
    response = generate_description(restaurant_data, visit_time)

    try:
        # 生成した結果をJSONに変換する
        description = json.loads(response)
        
        # データを整理する
        # TODO: dictからJSON文字列に変換する
        escaped_name = escape_string_for_json(name)
        activity_info = '{ "type": "meal", '
        activity_info += '"title": "' + escape_string_for_json(description["catchphrase"]) + '", '
        activity_info += '"description": "' + escape_string_for_json(description["description"]) + '", '
        activity_info += '"url": "' + restaurant_data["WEBSITE"][0] + '", '
        activity_info += '"datetime": "' + detetime_str_normalization(visit_time) + '", '
        activity_info += f'"location": {{ "name": "{escaped_name}", "latitude": {restaurant_data["LATITUDE"][0]}, "longitude": {restaurant_data["LONGITUDE"][0]} }}'
        activity_info += '}'
        result.append(activity_info)
    except Exception as e:
        continue

    # 進捗を更新する
    st.subheader(f"Generating plans...")
    generation_progress.progress((index + 1) / len(df))

# ここまでの結果を表示する
st.subheader("Complete. Here are the generated plans:")
generation_progress.progress(1.0)
with st.expander("Result"):
    st.write(result)
