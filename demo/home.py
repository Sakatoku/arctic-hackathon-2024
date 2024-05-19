import streamlit as st

## ページ表示

st.set_page_config(page_title="SAKATALK | Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="auto")

col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('''
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Josefin+Slab:ital,wght@0,100..700;1,100..700&family=Shalimar&display=swap" rel="stylesheet">
        <style>
        .app-title {
          font-family: "Josefin Slab", serif;
        }
        .app-title .app_name{
          color: #249edc;
        }
        .app-title .travel{
          font-family: "Shalimar", serif;
          font-size : 2.9rem;
          letter-spacing: 0.1em;
        }
        </style>
        <h1 class="app-title"><span class="app_name">SAKATALK</span> | <span class="travel">Travel Agency</span><h1>
    ''', unsafe_allow_html=True)

with col2:
    st.page_link("pages/1_get_customer_request.py", label="Let's go to your travel!", icon="🌍️")

'''
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


