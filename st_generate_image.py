# generate_image.py
# 画像を生成してダウンロードするサンプルプログラム

# Replicate library
import replicate

# OpenAI library
from openai import OpenAI

# Streamlit: https://www.streamlit.io/
import streamlit as st

# general libraries
import requests
import os

# ReplicateとOpenAIのAPIキーを環境変数に設定する
os.environ["REPLICATE_API_TOKEN"] = st.secrets["Replicate"]["apikey"]
os.environ["OPENAI_API_KEY"] = st.secrets["OpenAI"]["apikey"]

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Image Generator", page_icon=":paint:", layout="wide")
    st.title("Image Generator")

# プロンプトを生成する
def generate_prompt(situations):
    return f"""
    Create a photorealistic image of the following situations: {situations}.
    """
# Replicate APIを呼び出して画像を生成する
def generate_image_replicate(user_prompt):
    input = {
        "prompt": user_prompt
    }

    client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])
    output = client.run(
        "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
        input=input
    )
    return output[0]

# OpenAI APIを呼び出して画像を生成する
def generate_image_openai(user_prompt):
    # OpenAIクライアントを初期化する
    client = OpenAI()

    # プロンプトを生成する
    prompt = generate_prompt(user_prompt)

    # OpenAI APIを呼び出して画像を生成する
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    # 画像のURLを返り値から取得する
    image_url = response.data[0].url
    return image_url

# 画像を生成する
def generate_image(platform, user_prompt):
    if platform == "Replicate":
        return generate_image_replicate(user_prompt)
    else:
        return generate_image_openai(user_prompt)

# Main function
def main():
    # Initialize Streamlit
    init()

    # プラットフォームを選択する
    platforms = [
        "Replicate",
        "OpenAI"
    ]
    selected_platform = st.sidebar.selectbox("Platform", platforms, index=0)

    # ユーザプロンプトを取得する。ユーザプロンプトが空の場合はここで終了
    user_prompt = st.chat_input("Your prompt")
    if not user_prompt:
        return

    # ユーザプロンプトを表示する
    st.write(f"Prompt: {user_prompt}")

    # Generate image
    image_url = generate_image(selected_platform, user_prompt)

    # Display the image
    image = requests.get(image_url)
    st.image(image.content, use_column_width=True, caption="Generated Image")

if __name__ == '__main__':
    main()
