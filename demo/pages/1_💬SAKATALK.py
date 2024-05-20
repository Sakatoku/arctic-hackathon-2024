import ast
import time
import pandas as pd

import streamlit as st
import snowflake.connector
import snowflake.snowpark as snowpark

# Import submodules
import services.common

second_page_name = "2_🛫YOURPLAN.py"
avatar_image_name = "./resources/imgs/sakatoku.png"
logo_image_name = "./resources/imgs/logo.svg"

# Initialize Streamlit
def init():
    st.set_page_config(page_title="SakArctic Travel Agency", page_icon="🌍️", layout="wide", initial_sidebar_state="collapsed")
    # Show title
    services.common.show_title()

    # Show breadcrumb
    services.common.show_breadcrumb(1)

    # Customize chat display
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

# Functions to connect to Snowflake
@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflake connection information stored in session state in home.py
    connection = snowflake.connector.connect(
        user=st.session_state.snowflake_secrets["user"],
        password=st.session_state.snowflake_secrets["password"],
        account=st.session_state.snowflake_secrets["account"],
        role=st.session_state.snowflake_secrets["role"],
        warehouse=st.session_state.snowflake_secrets["warehouse"])
    # Create a Snowpark session
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

# Functions for Arctic Execution
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
    # Convert response to dictionary type
    response = ast.literal_eval(response)
    response = response["choices"][0]["messages"]
    return response

# Main function
def main():
    # Initialize Streamlit
    init()
    session = connect_snowflake()

    # Create variables for conversation history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Create variables for user requests
    if "result_request" not in st.session_state:
        # Japanese
        st.session_state.result_request = {
            "旅行の行き先": ["san-francisco"],
            "旅行の目的": "",
            "参加者の年齢": "",
            "参加者の人数": "",
            "旅行を開始する日付": "",
            "旅行を終了する日付": "",
            "旅行の予算": "",
            "旅行中に食べたいもの": "",
            "旅行先でしたいこと": ""
        }
        # English
        # st.session_state.result_request = {
        #     "Travel Destinations": ["san-francisco"],
        #     "Purpose of Trip": "",
        #     "Age of participants": "",
        #     "Number of participants": "",
        #     "Date to begin travel": "",
        #     "Date to end travel": "",
        #     "Travel Budget": "",
        #     "What to eat while traveling": "",
        #     "Things to do in the destination": ""
        # }

        # Consideration of questions for which answers have not been filled in
        st.session_state.next_question_title = ""
        for key, value in st.session_state.result_request.items():
            if value == "":
                st.session_state.next_question_title = key
                break
        # Japanese
        prompt_create_question = f'''
        #前提
        あなたはお客様に質問しながら、お客様の旅行プランを検討しています。
        次の質問では「{st.session_state.next_question_title}」が知りたいです。

        #依頼
        次の質問文を考えてください。
        出力はすべて英語でお願いします。

        #制約
        - 質問文の中には、必ずお客様の回答例を含めて出力すること
        - 必ず{st.session_state.next_question_title}に関する内容を質問してください。
        - 出力例の形式で出力してください。
        - 出力時には出力例と同じ文章は出力しないでください。

        #出力例
        旅行の予算はいくらですか？(例：10万円、100$など)

        質問：
        '''
        # English ----------
        #Assumption.
        # You are reviewing a customer's travel plans, asking questions of the customer.
        # You want to know "{st.session_state.next_question_title}" for the next question.

        #Request.
        # Please come up with the following question text.
        # All output should be in English.

        #Constraints
        # - Be sure to include an example of the customer's response in the output of the question text.
        # - Be sure to ask a question about {st.session_state.next_question_title}.
        # - Output in the format of the example output.
        # - Do not output the same text as the output example when outputting.

        # #Output example
        # What is your budget for the trip? (e.g. 100,000 yen, 100$, etc.)
        # ------------------
        messages = [{"role": "user", "content": prompt_create_question}]
        st.session_state.next_question_message = get_response(session, messages)
        st.session_state.messages.append({"role": "assistant", "content": st.session_state.next_question_message})


    # Show conversation history
    for message in st.session_state.messages:
        if message["role"] == "user":
            avatar_img = None
        else:
            avatar_img = avatar_image_name
        with st.chat_message(message["role"], avatar=avatar_img):
             st.markdown(message["content"])  

    prompt = st.chat_input("Please type your answer.")

    # Process after user input
    if prompt:
        # Add conversation to history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Show prompt
        with st.chat_message("user"):
            st.markdown(prompt)

        # check prompt
        if st.session_state.next_question_title != "":
            prompt_escaped = prompt.replace("'", "").replace(",", " ")
            # Japanese
            prompt_check_answer = f'''
            #前提
            あなたはお客様に質問しながら、お客様の旅行プランを検討しています。
            あなたは「{st.session_state.next_question_message}」と質問しました。
            お客様は「{prompt_escaped}」と回答しました。

            #依頼
            質問内容に対して回答が適当か判断し、適正な場合はTrue、適正でない場合はFalseと返答してください。

            #制約
            - 出力はTrueかFalseのいずれかのみとしてください。

            出力：
            '''
            # English ----------
            #Assumption.
            # You are reviewing a customer's travel plans, asking questions of the customer.
            # You asked "{st.session_state.next_question_message}".
            # The customer responded "{prompt_escaped}".

            #Request
            # Please judge whether the answer is appropriate to the question and reply True if appropriate or False if not.

            #Constraints
            # - Output should be either True or False only.

            # Output:
            # ------------------
            messages = [{"role": "user", "content": prompt_check_answer}]
            check_answer = get_response(session, messages).strip()
            if check_answer == "True":
                # 回答の抽出
                # Japanese
                prompt_extract_request = f'''
                #前提
                あなたはお客様に質問しながら、お客様の旅行プランを検討しています。
                あなたは「{st.session_state.next_question_message}」と質問しました。
                お客様は「{prompt_escaped}」と回答しました。

                #依頼
                お客様の回答から、質問に関連する部分のみ抜き出してください。
                出力は英語でお願いします。

                #制約
                - 必ずお客様の回答から抽出してください。
                - 必ず出力例の形式で出力してください。
                - 日付はMM/DDの形式にしてください。

                #出力例
                {{"{st.session_state.next_question_title}": "ユーザーの回答から抽出した結果を記載してください"}}

                出力：
                '''
                # English ----------
                #Assumption.
                # You are reviewing a customer's travel plans, asking questions of the customer.
                # You asked "{st.session_state.next_question_message}".
                # The customer responded "{prompt_escaped}".

                #Request
                # Please extract only the part of the customer's answer that is relevant to the question.
                # Output shield be in English.

                #Constraints
                # - Please be sure to extract from the customer's answers.
                # - Please be sure to output in the format shown in the example output.
                # - Date must be in MM/DD format.

                #Example output
                # {{"{st.session_state.next_question_title}": "Please describe the results extracted from user responses"}}

                # Output:
                # ------------------
                messages = [{"role": "user", "content": prompt_extract_request}]
                request = get_response(session, messages).replace("：", ":").strip()
                request = ast.literal_eval(request)
                request = list(request.values())[0]
                st.session_state.result_request[st.session_state.next_question_title] = [request]

                # Consideration of questions for which answers have not been filled in
                st.session_state.next_question_title = ""
                for key, value in st.session_state.result_request.items():
                    if value == "":
                        st.session_state.next_question_title = key
                        break
                # Set question if next question
                if st.session_state.next_question_title != "":
                    # Japanese
                    prompt_create_question = f'''
                    #前提
                    あなたはお客様に質問しながら、お客様の旅行プランを検討しています。
                    次の質問では「{st.session_state.next_question_title}」が知りたいです。

                    #依頼
                    次の質問文を考えてください。
                    出力はすべて英語でお願いします。

                    #制約
                    - 質問文の中には、必ずお客様の回答例を含めて出力すること
                    - 必ず{st.session_state.next_question_title}に関する内容を質問してください。
                    - 出力例の形式で出力してください。
                    - 出力時には出力例と同じ文章は出力しないでください。

                    #出力例
                    旅行の予算はいくらですか？(例：10万円、100$など)

                    質問：
                    '''
                    # English ----------
                    #Assumption.
                    # You are reviewing a customer's travel plans, asking questions of the customer.
                    # You want to know "{st.session_state.next_question_title}" for the next question.

                    #Request.
                    # Please come up with the following question text.
                    # All output should be in English.

                    #Constraints
                    # - Be sure to include an example of the customer's response in the output of the question text.
                    # - Be sure to ask a question about {st.session_state.next_question_title}.
                    # - Output in the format of the example output.
                    # - Do not output the same text as the output example when outputting.

                    #Output example
                    # What is your budget for the trip? (e.g. 100,000 yen, 100$, etc.)

                    # Question:
                    # ------------------
                    messages = [{"role": "user", "content": prompt_create_question}]
                    st.session_state.next_question_message = get_response(session, messages)
                    st.session_state.messages.append({"role": "assistant", "content": st.session_state.next_question_message})
                    with st.chat_message("assistant", avatar=avatar_image_name):
                        st.markdown(st.session_state.next_question_message)
                # If all responses are obtained, display the results and go on to the next step.
                else:
                    thanks_msg = f'''
                    Thank you for your response!  
                    I will generate a plan with the following information✈️
                    '''
                    df = pd.DataFrame.from_dict(st.session_state.result_request).T
                    df.index = ["destination",
                                "purpose",
                                "traveler_age",
                                "number_of_people",
                                "travel_start_date",
                                "travel_end_date",
                                "budget",
                                "food_preferences",
                                "activity_preferences"
                                ]
                    with st.chat_message("assistant", avatar=avatar_image_name):
                        st.markdown(thanks_msg)
                        st.dataframe(df, column_config={"0": "回答内容"}, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": thanks_msg})
                    # For subsequent processing
                    result_request_txt = '{'
                    for row in df.itertuples():
                        result_request_txt += f'"{row[0]}": "{row[1]}",'
                    result_request_txt += '}'
                    st.session_state.customer_request = result_request_txt
                    st.write(st.session_state.customer_request)
                    st.snow()
                    time.sleep(5)
                    st.switch_page(f"pages/{second_page_name}")
            # When Failed
            else:
                error_msg = "My apologies. Could you please answer again?"
                with st.chat_message("assistant", avatar=avatar_image_name):
                        st.markdown(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        # Reactions after completion of responses
        else:
            thanks_msg = "Thank you for your response!"
            with st.chat_message("assistant", avatar=avatar_image_name):
                st.markdown(thanks_msg)
                st.session_state.messages.append({"role": "assistant", "content": thanks_msg})


if __name__ == '__main__':
    main()