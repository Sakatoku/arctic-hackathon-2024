# 環境構築コマンド
# conda create -n arctic python=3.8
# conda activate arctic
# pip install snowflake-connector-python snowflake-snowpark-python snowflake-ml-python[all] streamlit tiktoken

# 実行コマンド
# streamlit run arctic_st.py

import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex
import json
import tiktoken

# ローカルPython環境からSnowflakeに接続するための関数
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

# 画面レイアウトを設定
st.set_page_config(layout="wide")

# TikTokenでトークン数を見積もる。Snowflake Arcticのトークナイザではないので参考値
def estimate_token_count(prompt):
    encoding1 = tiktoken.encoding_for_model("gpt-4")
    tokens1 = encoding1.encode(prompt)
    return len(tokens1)

# Temperatureを取得する
temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.1)

# ユーザプロンプトを取得する。ユーザプロンプトが空の場合はここで終了
user_prompt = st.chat_input("Your prompt")
if not user_prompt:
    st.stop()

# 推定トークン数を表示する
token_count1 = estimate_token_count(user_prompt)
st.write(f'推定トークン数(GPT-4): {token_count1}')

# ユーザプロンプトを表示
with st.chat_message("user"):
    st.write(user_prompt)

# Snowflakeに接続する
session = connect_snowflake()

# SQLでSnowflake Cortex LLM Functionsを呼び出す
def cortex_complete(session, model_name, prompt):
    # 注意！本来はSQLインジェクション攻撃ができないように適切に文字列を処理することが望ましい
    # プロンプトをエスケープする
    prompt = prompt.replace('\'', '\\\'')
    # JSONで入力すると出力のときにメタデータが得られる
    cmd = f"select snowflake.cortex.complete('{model_name}', [{{'role': 'user', 'content': '{prompt}'}}], {{'temperature': {temperature}}}) as RESPONSE"
    # session.sqlの出力はROWのリストとして得られる
    # ROWの"RESPONSE"キーにJSON文字列が格納されている。キーは必ずアッパーケースになることに注意
    df_response = session.sql(cmd).collect()
    print(df_response)
    json_response = json.loads(df_response[0]["RESPONSE"])
    return json_response

# Snowflake Cortex LLM FunctionsのJSONからレスポンスだけを抽出する
def parse_llm_response(j):
    return j["choices"][0]["messages"]

# Snowflake Cortex LLM Functionsを呼び出してレスポンスを取得する
response = cortex_complete(session, "snowflake-arctic", user_prompt)

# レスポンスを表示
with st.chat_message("arctic"):
    st.write(parse_llm_response(response))
    with st.expander("詳細", expanded=False):
        st.write(response)
