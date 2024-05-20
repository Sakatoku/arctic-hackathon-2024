import ast
import time
from bs4 import BeautifulSoup

import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark

# Import submodules
import services.common

second_page_name = "2_🛫YOURPLAN.py"
avatar_image_name = "./resources/imgs/sakatoku.png"
MAX_CONV_LENGTH = 22

# Initialize Streamlit
def init():
    st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="collapsed")

    # Show title
    services.common.show_title()

    # Show breadcrumb
    services.common.show_breadcrumb(1)

    st.sidebar.title('Json')

    # チャットの表示をカスタマイズ
    st.markdown('''
                <style>
                .stChatMessage{
                    width: fit-content;
                    padding-right: 16px
                }
                .stChatMessage p{
                    width: fit-content;
                }
                .stChatMessage:nth-child(even){
                    background: #249EDC;
                    margin: 0 0 0 auto;
                }
                .stChatMessage:nth-child(even) p{
                    color: #fff !important;
                }
                .stChatMessage:nth-child(even) div:has(svg){
                    display: none;
                }
                .stChatMessage:nth-child(odd){
                    background: #eee;
                }
                .stChatMessage:nth-child(odd) p{
                    color: #333 !important;
                }
                </style>
    ''', unsafe_allow_html=True)

# ローカルPython環境からSnowflakeに接続するための関数
@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflakeの接続情報はhome.pyでセッションステートに保存されたものを使う
    connection = snowflake.connector.connect(
        user=st.session_state.snowflake_secrets["user"],
        password=st.session_state.snowflake_secrets["password"],
        account=st.session_state.snowflake_secrets["account"],
        role=st.session_state.snowflake_secrets["role"],
        warehouse=st.session_state.snowflake_secrets["warehouse"])

    # Snowparkセッションを作成する
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

# Arctic実行用の関数
def get_response(session, messages):
    sql = f'''
    SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic',
        {messages},
        {{
            'temperature': 0.3,
            'top_p': 0.9
        }});
    '''
    response = session.sql(sql).to_pandas().iloc[0,0]
    # レスポンスを変換
    response = ast.literal_eval(response)
    response = response["choices"][0]["messages"]
    soup = BeautifulSoup(response, 'html.parser')
    # 結果の形式判定
    if not soup.find("question") or not soup.find("request"):
        result = {
            "response": False,
            "request": False,
            "question": False,
            "finish": False
        }
    else:
        question = soup.find("question").contents[0]
        request = soup.find("request").contents[0]
        request = request.strip()
        finish = soup.find("finish")
        result = {
            "response": response,
            "request": request,
            "question": question,
            "finish": finish
        }
    return result


# Main function
def main():
    # Initialize Streamlit
    init()

    session = connect_snowflake()

    # 会話履歴表示用の変数
    if "messages_display" not in st.session_state:
        st.session_state.messages_display = []

    # 会話履歴処理用の変数
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
            - userの回答に関して、再確認する必要はありません。
            - 質問はJSONに記載したキーの内容を確認する質問のみとしてください。
            - 全ての回答が得られた場合は、感謝を伝える文を、<question></question>の中に、JSONは全ての属性を含めて<request></request>の中に、出力の最後に"<finish>finish</finish>"を追加してください。
            - 必ず下記のJSONの形式で出力してください。
            - 回答は英語でお願いします。
            # JSON
            <request>{ "destination": "san-francisco", "purpose": "", "traveler": { "age": "", "number_of_people": "" }, "travel_dates": {"start_date": "", "end_date": ""}, "budget": "", "food_preferences": "", "activity_preferences": ""} </request>
        '''
        st.session_state.messages.append({"role": "user", "content": first_prompt})
        messages=[]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": m["content"]})
        result = get_response(session, messages)
        # 会話を履歴に追加
        st.session_state.messages.append({"role": "assistant", "content": result["response"]})
        st.session_state.messages_display.append({"role": "assistant", "content": result["question"]})

    # 会話履歴を表示
    for i, message in enumerate(st.session_state.messages_display):
        if message["role"] == "user":
            avatar_img = None
        else:
            avatar_img = avatar_image_name
        with st.chat_message(message["role"], avatar=avatar_img):
             if i == 0:
                 st.markdown("Let's plan a trip together!")
             st.markdown(message["content"])  

    # 入力を受付
    prompt = st.chat_input("Please type your answer.")

    # 入力後の処理
    if prompt:
        # 会話を履歴に追加
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.messages_display.append({"role": "user", "content": prompt})

        # 入力を表示
        with st.chat_message("user"):
            st.markdown(prompt)

        # Arctic用に会話履歴を作成
        messages=[]
        for m in st.session_state.messages:
            messages.append({"role": m["role"], "content": f'"{m["content"]}"'})

        # Arctic実行
        result = get_response(session, messages)
        if result['response']:
            st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            st.session_state.messages_display.append({"role": "assistant", "content": result["question"]})
            # 入力内容を表示
            with st.chat_message("assistant", avatar=avatar_image_name):
                st.sidebar.json(result["request"])
                st.markdown(result["question"])
        else:
            with st.chat_message("assistant", avatar=avatar_image_name):
                error_msg = 'I did not understand it well. Could you please answer again?'
                st.markdown(error_msg)
                st.session_state.messages_display.append({"role": "assistant", "content": error_msg})

        # 完了判定
        if result['finish'] or len(st.session_state.messages) > MAX_CONV_LENGTH:
            st.sidebar.subheader("Fix!!")
            st.snow()

            st.session_state.customer_request = result["request"] 
            time.sleep(4)
            st.switch_page(f"pages/{second_page_name}")

if __name__ == '__main__':
    main()