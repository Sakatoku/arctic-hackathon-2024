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

# OpenAIクライアントを初期化する
client = OpenAI()

# 7時から20時までの各時間について、アクティビティを列挙したdict
activities = {
    "7:00": "watching the sunrise",
    "8:00": "having breakfast",
    "9:00": "exploring a local market",
    "10:00": "visiting a museum",
    "11:00": "taking a guided tour",
    "12:00": "having lunch at a casual italian restaurant",
    "13:00": "relaxing in a park",
    "14:00": "shopping at boutiques",
    "15:00": "enjoying a coffee break",
    "16:00": "visiting a historical site",
    "17:00": "taking a cooking class",
    "18:00": "having dinner at a steakhouse",
    "19:00": "attending a cultural event",
    "20:00": "exploring the nightlife",
}

# プロンプトを生成する
def generate_prompt(time_of_day, activity):
    return f"""
    Create a photorealistic image of a person sightseeing in San Francisco during {time_of_day}. 
    The scene should prominently feature a well-known San Francisco landmark, such as the Golden Gate Bridge, Alcatraz Island, or Fisherman's Wharf. 
    The person should be engaged in {activity}, capturing the essence of enjoying the city's attractions. 
    Ensure the background includes elements characteristic of San Francisco, such as hilly streets, cable cars, or Victorian houses. 
    The overall mood should be vibrant and lively, reflecting the unique atmosphere of the city.
    """

# アクティビティを列挙したdictの各要素について、画像を生成してダウンロードする
for time_of_day, activity in activities.items():
    # プロンプトを生成する
    prompt = generate_prompt(time_of_day, activity)

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

    # ファイル名を生成する。7:00 -> photo_0700.jpg
    filename = "photo_" + time_of_day.replace(":", "") + ".jpg"

    # 画像をダウンロードする
    image = requests.get(image_url)
    with open(f'temp/{filename}', 'wb') as f:
        f.write(image.content)
        print(f"Downloaded {filename}")
