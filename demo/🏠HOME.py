import streamlit as st

## ページ表示

st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="auto")

col1, col2 = st.columns([4, 1])
with col1:
    st.image("./resources/imgs/logo.svg")

with col2:
    st.markdown('''
    <style>
        .stPageLink a{
          background-color: #249edc;
          transition: all .3s ease;
          height: 55px;
        }
        .stPageLink a p{
          color: #fff !important;
        }
        .stPageLink a:hover{
          background-color: #205f7f;
        }
    </style>
    ''', unsafe_allow_html=True)
    st.page_link("pages/1_💬SAKATALK.py", label="Let's go to your travel!", icon="🌍️")

'''
---
## Description
This application is a trip plan generator application.  
It listens to the user's requests in a chat format and creates a trip plan based on the content of the interview.

## Sample UI
'''
col1, col2 = st.columns([1, 4])
with col1:
  st.caption('Chat UI')
  st.image("./resources/imgs/app_image_chat.png")

with col2:
  st.caption('Plan UI')
  st.image("./resources/imgs/app_image_plan.png")


