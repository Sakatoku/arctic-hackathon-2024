import json
import requests
from bs4 import BeautifulSoup
from getpass import getpass

import pandas as pd
import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark
from snowflake.snowpark import Session

## pip install bs4 snowflake-snowpark-python pandas

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


def check_ng(input_text: str) -> bool:
    ng_list = ["403 Forbidden", "404 Not Found", "Not Acceptable", "Access Denied", "Connection timed out" ]
    if len(input_text) < 30:
        return True
    for ng_word in ng_list:
        if ng_word in input_text:
            return True
    
    return False

def get_page_text(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        if response.headers['Content-Type'].lower().startswith('text/html'):
            return BeautifulSoup(response.text, 'html.parser').get_text(separator=', ', strip=True)
    except:
        return None
    return None

def get_summarized_web_df(session: Session, df: pd.DataFrame, col_name: str="WEBSITE") -> pd.DataFrame:
    for idx, web_url in df[col_name].items():
        if web_url is None:
            continue
        page_text = get_page_text(web_url)
        
        if page_text is None or check_ng(page_text):
            print(f"{page_text} is not valid.")
            continue
        
        try:
            page_text_escaped = page_text.replace("'", "\\'").replace("\n", "")
            df_summarized = session.sql(f"select snowflake.cortex.summarize('{page_text_escaped}') as WEB_SUMMARY")
            df.at[idx, "WEB_SUMMARY"] = df_summarized.to_pandas()["WEB_SUMMARY"].iloc[0]
        except:
            continue

    return df

def write_summarized_table_website(session: Session, input_table: str, col_name: str, output_table: str) -> None:
    df = session.table(input_table).to_pandas()
    df = get_summarized_web_df(session, df, col_name=col_name)
    session.write_pandas(df, output_table, auto_create_table=True, overwrite=True)

def main():
    session = connect_snowflake()

    write_summarized_table_website(session, "CL_RESTAURANTS", "WEBSITE", "CL_RESTAURANTS_SUMMARIZED")
    write_summarized_table_website(session, "TOURISM_SPOTS", "WEBSITE", "TOURISM_SPOTS_SUMMARIZED")

if __name__ == "__main__":
    main()
