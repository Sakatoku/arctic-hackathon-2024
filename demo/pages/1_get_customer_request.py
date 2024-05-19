import ast
from bs4 import BeautifulSoup

import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark

from services.inquiry_plan_2 import get_requested_df

second_page_name = "2_get_tour_plan.py"
avatar_image_name = "./resources/imgs/sakatoku.png"
MAX_CONV_LENGTH = 14

# Initialize Streamlit
def init():
    st.set_page_config(page_title="SakArctic Travel Agency", page_icon=":snowflake:", layout="wide", initial_sidebar_state="expanded")
    st.title(":blue[SakA]rctic Travel Agency")
    st.caption("This application is for hearing information for San Francisco travel plan consideration.")
    st.divider()
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

# Arctic実行用の関数
def get_response(session, messages):
    response = session.sql(f'''
    SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic',
        {messages},
        {{
            'temperature': 0.3,
            'top_p': 0.9
        }});
        ''').to_pandas().iloc[0,0]
    # レスポンスを変換
    response = ast.literal_eval(response)
    response = response["choices"][0]["messages"]
    soup = BeautifulSoup(response, 'html.parser')
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
            - userの回答に関して、確認する必要はありません。
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
            messages.append({"role": m["role"], "content": m["content"]})

        # Arctic実行
        result = get_response(session, messages)
        st.session_state.messages.append({"role": "assistant", "content": result["response"]})
        st.session_state.messages_display.append({"role": "assistant", "content": result["question"]})

        # 入力内容を表示
        with st.chat_message("assistant", avatar=avatar_image_name):
            st.sidebar.json(result["request"])
            st.markdown(result["question"])

        # 完了判定
        if result['finish'] or len(st.session_state.messages) > MAX_CONV_LENGTH:
            st.sidebar.subheader("Fix!!")
            st.snow()

            st.session_state.customer_request = result["request"]
            st.session_state.restaurants_df, st.session_state.tours_df = get_requested_df(session, st.session_state.customer_request) 

            st.switch_page(f"pages/{second_page_name}")

if __name__ == '__main__':
    main()