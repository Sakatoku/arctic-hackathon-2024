# Streamlit: https://www.streamlit.io/
import streamlit as st
import pandas as pd

# Snowflake and Snowpark
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex

# General libraries
import ast
from bs4 import BeautifulSoup

from services.inquiry_plan_2 import get_requested_df

second_page_name = "2_get_tour_plan.py"

# Initialize Streamlit
def init():
    st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="auto")
    st.image("resources/imgs/logo.png", width=800)
    # st.set_page_config(page_title="Arctic", page_icon=":snowflake:", layout="wide", initial_sidebar_state="collapsed")
    # st.title(":blue[SakA]rctic")
    st.caption("This application is for hearing information for San Francisco travel plan consideration.")
    st.divider()
    st.sidebar.title('Json')

    st.markdown('''
                <style>
                .stChatMessage{
                    width: fit-content;
                    padding-right: 16px
                }
                .stChatMessage p{
                    width: fit-content;
                }
                .stChatMessage:nth-child(odd){
                    background: #249EDC;
                    margin: 0 0 0 auto;
                }
                .stChatMessage:nth-child(odd) p{
                    color: #fff !important;
                }
                .stChatMessage:nth-child(odd) div:has(svg){
                    display: none;
                }
                .stChatMessage:nth-child(even){
                    background: #eee;
                }
                </style>
    ''', unsafe_allow_html=True)



# ローカルPython環境からSnowflakeに接続するための関数
@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflakeに接続する
    # Snowflakeの接続情報はStreamlitのシークレット(.streamlit/secret.toml)に保存しておく
    connection = snowflake.connector.connect(
        user=st.secrets["SnowflakeProd"]["user"],
        password=st.secrets["SnowflakeProd"]["password"],
        account=st.secrets["SnowflakeProd"]["account"],
        role=st.secrets["SnowflakeProd"]["role"],
        warehouse=st.secrets["SnowflakeProd"]["warehouse"])

    # Snowparkセッションを作成する
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

def get_response(session, prompt):
    response = cortex.Complete("snowflake-arctic", prompt)
    return response

# Main function
def main():
    # Initialize Streamlit
    init()

    # Snowflakeに接続する
    session = connect_snowflake()

    if "question_continue" not in st.session_state:
        st.session_state.question_continue = True

    if "messages_display" not in st.session_state:
        st.session_state.messages_display = []

    # セッション内のメッセージが指定されていない場合のデフォルト値
    if "messages" not in st.session_state:
        st.session_state.messages = []
        first_prompt ='''
旅行プランを考えるLLMアプリケーションを構築したいです。そこで、あなたはその質問を考える役割を担ってもらいます。
クライアントとの複数の対話に基づいて、下記のJSONを埋めていきたいです。その際の質問文を考えつつ、JSONを埋めていってください。このとき、質問は、<question></question>の中に、JSONは<request></request>の中に記述してください。
# 制約
- 1回の出力で<question></question>、<request></request>を1つのみ出力してください。
- 属性が埋まったら次の属性の質問をしてください。
- 必ずすべてのキー属性について質問してください。
- 過去にした質問と同じ質問や類似した質問は禁止です。
- userの回答に関して、確認する必要はありません。
- 質問はJSONに記載したキーの内容を確認する質問のみとしてください。
- 全ての回答が得られた場合は、感謝を伝える文を、<question></question>の中に、JSONは全ての属性を含めて<request></request>の中に、出力の最後に"<finish>finish</finish>"を追加してください。
- 必ず下記のJSONの形式で出力してください。
# JSON
<request>{ "destination": "san-francisco", "purpose": "", "traveler": { "age": "", "number_of_people": "" }, "travel_dates": {"start_date": "", "end_date": ""}, "budget": "", "food_preferences": "", "activity_preferences": ""} </request>

        '''
        st.session_state.messages.append({"role": "user", "content": first_prompt})

        messages=[]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})

        response = session.sql(f'''
        SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic',
            {messages},
            {{
                'temperature': 0.3,
                'top_p': 0.9
            }});
          ''').to_pandas().iloc[0,0]
        response = ast.literal_eval(response)
        response = response["choices"][0]["messages"]
        soup = BeautifulSoup(response, 'html.parser')
        question = soup.find("question").contents[0]
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.messages_display.append({"role": "assistant", "content": question})

    # 以前のメッセージを表示 
    for i, message in enumerate(st.session_state.messages_display):
        if message["role"] == "user":
            avatar_img = None
        else:
            avatar_img = "./resources/imgs/sakatoku.png"
        with st.chat_message(message["role"], avatar=avatar_img):
             if i == 0:
                 st.markdown("Let's plan a trip together!")
             st.markdown(message["content"])  

    if st.session_state.question_continue:
      # ユーザーからの新しい入力を取得
      prompt = st.chat_input("Please type your answer.")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages_display.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="./resources/imgs/sakatoku.png"):
            messages=[]
            for m in st.session_state.messages:
                messages.append({"role": m["role"], "content": m["content"]})
            response = session.sql(f'''
            SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic',
                {messages},

                {{
                'temperature': 0.3,
                'top_p': 0.9
                }});
            ''').to_pandas().iloc[0,0]
            response = ast.literal_eval(response)
            response = response["choices"][0]["messages"]
            soup = BeautifulSoup(response, 'html.parser')
            question = soup.find("question").contents[0]
            request = soup.find("request").contents[0]
            request = request.strip()
            finish = soup.find("finish")
            if finish:
                st.sidebar.write('finish')
                st.balloons()
                st.session_state.question_continue = False
                st.session_state.customer_request = request

                ## DF作成処理を実行していく。ための関数を作る。実行したらデータフレームが2つ返ってくるイメージ。
                
                st.session_state.restaurants_df, st.session_state.tours_df = get_requested_df(session, request) 

                ## 終わったら強制ページ遷移。
                st.switch_page(f"pages/{second_page_name}")

            st.sidebar.json(request)
            st.write(question)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.messages_display.append({"role": "assistant", "content": question})


if __name__ == '__main__':
    main()