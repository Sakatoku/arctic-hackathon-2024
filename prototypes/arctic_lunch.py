# arctic_lunch.py
# 営業時間を示す入力文字列から朝営業・昼営業・夜営業をやっている確認するプログラム

# Streamlit: https://www.streamlit.io/
import streamlit as st

# Snowflake and Snowpark
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex

# General libraries
import json
import re

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Arctic Lunch", page_icon=":snowflake:", layout="wide")
    st.title("Are you open for ...?")

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
    st.write(j)
    return j["choices"][0]["messages"]

# 正規表現で数字を抜き出す
def parse_time(str, tag):
    # 正規表現で<tag>(dd):(dd)</tag>の数字をパースする
    time = re.search(rf'<{tag}>(\d+):(\d+)</{tag}>', str)
    if time and time.groups() and len(time.groups()) == 2:
        return int(time.groups()[0]) * 60 + int(time.groups()[1])
    return None

# Main function
def main():
    # Initialize Streamlit
    init()

    # Snowflakeに接続する
    session = connect_snowflake()

    # Temperatureを取得する
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.1, step=0.1)

    # サンプル文字列を表示
    st.write("Example: Mo-Th 15:00-22:00; Fr 12:00-22:00; Sa,Su 10:00-22:00")
    # 入力が空の場合は終了
    opening_hours = st.text_input("Opening Hours", "Mo-Th 15:00-22:00; Fr 12:00-22:00; Sa,Su 10:00-22:00")
    if opening_hours == "":
        st.stop()

    # プロンプトを合成する
    # このプロンプトは失敗する：f"This is opening hours of a store. Does this store open for lunch(11:00-13:59)? If so, type 1. If not, type 0.\n<opening_hours>{opening_hours}</opening_hours>"
    # このプロンプトは失敗する：f"Description between <business_hour>tag is business hours of a store. Typically, business hours are described in the format (opening_time)-(closing_time).\nPlease classify the classes according to the following 3 rules:\nRule 1. If (opening_time) is between 10:00-24:00, output <result>0</result>.\nRule 2. If (closing_time) is between 00:00-06:00, output <result>0</result>.\nRule 3. If neither Rule 1 nor Rule 2 fires, output <result>1</result>.\nYou shall output result, and explain in detail which rules were fired.\n<business_hours>{opening_hours}</business_hours>"
    # 以下のプロンプトは比較的安定する：f"Description between <business_hour>tag is business hours of a store. Typically, business hours are described in the format (opening_time)-(closing_time). It is sometimes accompanied by the day of the week.\nDescription between <weekday>tag is designated day of the week.\nPlease convert business hours of designate day of the week the following format: <open>(opening_time)</open><close>(closing_time)</close>\n<business_hours>{opening_hours}</business_hours><weekday>{weekday}</weekday>"
    weekday = "Any"
    prompt = f"Description between <business_hour>tag is business hours of a store. Typically, business hours are described in the format (opening_time)-(closing_time). It is sometimes accompanied by the day of the week.\nDescription between <weekday>tag is designated day of the week.\n<business_hours>{opening_hours}</business_hours>\n<weekday>{weekday}</weekday>\nPlease convert business hours of designate day of the week the following format: <open>(opening_time)</open><close>(closing_time)</close>"
    st.subheader("Prompt: ")
    st.write(prompt)

    # Snowflake Cortex LLM Functionsを呼び出してレスポンスを取得する
    response = cortex_complete(session, "snowflake-arctic", prompt, temperature)
    st.subheader("Response: ")
    message = parse_llm_response(response)

    # 時間をパースする
    open_time = parse_time(message, "open")
    close_time = parse_time(message, "close")
    do_breakfast = (open_time <= 10 * 60) and (close_time >= 6 * 60)
    do_lunch = (open_time <= 15 * 60) and (close_time >= 10 * 60)
    do_dinner = (open_time <= 24 * 60) and (close_time >= 18 * 60)

    # 結果を表示
    st.subheader("Result: ")
    st.write(f"朝営業: {do_breakfast}")
    st.write(f"昼営業: {do_lunch}")
    st.write(f"夜営業: {do_dinner}")

if __name__ == '__main__':
    main()
