import streamlit as st

# Import submodules
import services.common

# ページ表示
st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="collapsed")

# シークレットの初期化
with st.sidebar:
    token_sets = [ "Snowflake", "Reserved1", "Reserved2" ]
    token_set = st.selectbox("Select Secrets", token_sets)
    st.session_state.snowflake_secrets = st.secrets[token_set]
  
col1, col2 = st.columns([4, 1])

# Show title
with col1:
    services.common.show_title()

# Show button for starting application 
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
    st.page_link("pages/1_💬SAKATALK.py", label="Let's make a plan for your trip!", icon="🌍️")

# Show breadcrumb
services.common.show_breadcrumb(0)

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
