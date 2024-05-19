import streamlit as st

## ページ表示

st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="auto")
st.image("resources/imgs/logo.png", width=800)
# st.title("Tour App")
st.caption("This application is for hearing information for San Francisco travel plan consideration.")

st.write("なにか画像を貼る")
st.write("なにか説明を書く")

st.page_link("pages/1_get_customer_request.py", label="Let's go to your travel!", icon="🌍️")

