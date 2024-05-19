# 環境構築コマンド
# conda create -n arctic python=3.8
# conda activate arctic
# pip install snowflake-connector-python snowflake-snowpark-python snowflake-ml-python[all] streamlit tiktoken

# 実行コマンド
# streamlit run arctic_st.py

# Streamlit: https://www.streamlit.io/
import streamlit as st

# Snowflake and Snowpark
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex

# OpenAI Tokenizer library
import tiktoken

# General libraries
import json

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Snowflake Arctic Prompt", page_icon=":snowflake:", layout="wide")
    st.title("Snowflake Arctic Prompt")

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

# ログを表示する
@st.experimental_fragment
def show_logs():
    if "log" not in st.session_state or st.session_state.log is None:
        st.session_state.log = ""
    st.text_area("Logs", value=st.session_state.log, height=600, disabled=True)

# ログを追加する
def append_log(new_log=""):
    if "log" not in st.session_state or st.session_state.log is None:
        st.session_state.log = ""
    if new_log != "":
        if len(st.session_state.log) > 0:
            st.session_state.log += "\n"
        st.session_state.log += new_log

# TikTokenでトークン数を見積もる。Snowflake Arcticのトークナイザではないので参考値
def estimate_token_count(prompt):
    encoding1 = tiktoken.encoding_for_model("gpt-4")
    tokens1 = encoding1.encode(prompt)
    return len(tokens1)

# SQLでSnowflake Cortex LLM Functionsを呼び出す
def cortex_complete(session, model_name, prompt, temperature):
    # 注意！本来はSQLインジェクション攻撃ができないように適切に文字列を処理することが望ましい
    # プロンプトをエスケープする
    prompt = prompt.replace('\'', '\\\'')
    # JSONで入力すると出力のときにメタデータが得られる
    cmd = f"select snowflake.cortex.complete('{model_name}', [{{'role': 'user', 'content': '{prompt}'}}], {{'temperature': {temperature}}}) as RESPONSE"
    # session.sqlの出力はROWのリストとして得られる
    # ROWの"RESPONSE"キーにJSON文字列が格納されている。キーは必ずアッパーケースになることに注意
    df_response = session.sql(cmd).collect()
    json_response = json.loads(df_response[0]["RESPONSE"])
    return json_response

# Snowflake Cortex LLM FunctionsのJSONからレスポンスだけを抽出する
def parse_llm_response(j):
    return j["choices"][0]["messages"]

# Main function
def main():
    # Initialize Streamlit
    init()

    # Snowflakeに接続する
    session = connect_snowflake()

    # LLMモデルを選択する
    # https://docs.snowflake.com/en/sql-reference/functions/complete-snowflake-cortex#arguments
    models = [
        "snowflake-arctic",
        "mistral-large",
        "reka-flash",
        "reka-core",
        "mixtral-8x7b",
        "llama2-70b-chat",
        "llama3-8b",
        "llama3-70b",
        "mistral-7b",
        "gemma-7b"
    ]
    selected_model = st.sidebar.selectbox("Model", models, index=0)

    # Temperatureを指定させる
    temperatures_with_label = {
        "0.0": 0.0,
        "0.1": 0.1,
        "0.2": 0.2,
        "0.3": 0.3,
        "0.4": 0.4,
        "0.5": 0.5,
        "0.6": 0.6,
        "0.7": 0.7,
        "0.8": 0.8,
        "0.9": 0.9,
        "1.0": 1.0,
    }
    temperature_label = st.sidebar.select_slider("Temperature", temperatures_with_label.keys())
    temperature = temperatures_with_label[temperature_label]

    try:
        # ユーザプロンプトを取得する。ユーザプロンプトが空の場合はここで終了
        user_prompt = st.chat_input("Your prompt")
        if not user_prompt:
            return

        # 推定トークン数を表示する
        token_count = estimate_token_count(user_prompt)
        append_log(f"推定トークン数(GPT-4): {token_count}")

        # ユーザプロンプトを表示
        with st.chat_message("user"):
            st.write(user_prompt)

        # Snowflake Cortex LLM Functionsを呼び出してレスポンスを取得する
        response = cortex_complete(session, selected_model, user_prompt, temperature)

        # レスポンスを表示
        with st.chat_message("arctic"):
            st.write(parse_llm_response(response))
            with st.expander("詳細", expanded=False):
                st.write(response)
    
    finally:
        with st.sidebar:
            show_logs()

if __name__ == '__main__':
    main()
