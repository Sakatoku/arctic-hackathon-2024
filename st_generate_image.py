# generate_image.py
# 画像を生成してダウンロードするサンプルプログラム

# OpenAI library
from openai import OpenAI

# Streamlit: https://www.streamlit.io/
import streamlit as st

# general libraries
import requests
import os

# OpenAI APIキーを環境変数に設定する
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

# 画像を生成する
def generate_image(client, user_prompt):
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

# # アクティビティを列挙したdictの各要素について、画像を生成してダウンロードする
# for time_of_day, activity in activities.items():
#     # プロンプトを生成する
#     prompt = generate_prompt(time_of_day, activity)

#     # OpenAI APIを呼び出して画像を生成する
#     response = client.images.generate(
#         model="dall-e-3",
#         prompt=prompt,
#         size="1024x1024",
#         quality="standard",
#         n=1,
#     )

#     # 画像のURLを返り値から取得する
#     image_url = response.data[0].url

#     # ファイル名を生成する。7:00 -> photo_0700.jpg
#     filename = "photo_" + time_of_day.replace(":", "") + ".jpg"

#     # 画像をダウンロードする
#     image = requests.get(image_url)
#     with open(f'temp/{filename}', 'wb') as f:
#         f.write(image.content)
#         print(f"Downloaded {filename}")

# Main function
def main():
    # Initialize Streamlit
    init()

    # OpenAIクライアントを初期化する
    client = OpenAI()

    # ユーザプロンプトを取得する。ユーザプロンプトが空の場合はここで終了
    user_prompt = st.chat_input("Your prompt")
    if not user_prompt:
        return

    # ユーザプロンプトを表示する
    st.write(f"Prompt: {user_prompt}")

    # Generate image
    image_url = generate_image(client, user_prompt)

    # Display the image
    image = requests.get(image_url)
    st.image(image.content, use_column_width=True, caption="Generated Image")

if __name__ == '__main__':
    main()
