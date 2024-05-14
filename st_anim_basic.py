# st_anim_basic.py
# Streamlitによるアニメーション表現の基礎検証

# Streamlit: https://www.streamlit.io/
import streamlit as st

# general libraries
import pandas as pd
import time
import datetime

# スライダーをアニメーションさせる範囲
dt_start = datetime.datetime(2024, 6, 3, 0, 0, 0, 0)
dt_end = datetime.datetime(2024, 6, 4, 0, 0, 0, 0)

# スライダーのラベルフォーマット
slider_format = "MM/DD hhA"

# 表示するランドマーク一覧
landmarks = [
    {"name": "Golden Gate Bridge", "latitude": 37.8199, "longitude": -122.4783},
    {"name": "Fisherman's Wharf", "latitude": 37.8080, "longitude": -122.4177},
    {"name": "Alcatraz Island", "latitude": 37.8270, "longitude": -122.4230},
    {"name": "Golden Gate Park", "latitude": 37.7694, "longitude": -122.4862},
    {"name": "Pier 39", "latitude": 37.8087, "longitude": -122.4098},
    {"name": "Lombard Street", "latitude": 37.8021, "longitude": -122.4186},
    {"name": "Union Square", "latitude": 37.7879, "longitude": -122.4074},
    {"name": "Chinatown", "latitude": 37.7941, "longitude": -122.4078},
    {"name": "Coit Tower", "latitude": 37.8024, "longitude": -122.4058},
    {"name": "Palace of Fine Arts", "latitude": 37.8021, "longitude": -122.4488},
    {"name": "San Francisco Museum of Modern Art", "latitude": 37.7857, "longitude": -122.4011},
    {"name": "Ghirardelli Square", "latitude": 37.8059, "longitude": -122.4227},
    {"name": "AT&T Park", "latitude": 37.7786, "longitude": -122.3893},
    {"name": "Exploratorium", "latitude": 37.8009, "longitude": -122.3984},
    {"name": "Transamerica Pyramid", "latitude": 37.7952, "longitude": -122.4028},
    {"name": "California Academy of Sciences", "latitude": 37.7699, "longitude": -122.4661},
    {"name": "Japanese Tea Garden", "latitude": 37.7702, "longitude": -122.4708},
    {"name": "Baker Beach", "latitude": 37.7936, "longitude": -122.4837},
    {"name": "Dolores Park", "latitude": 37.7596, "longitude": -122.4270},
    {"name": "Twin Peaks", "latitude": 37.7544, "longitude": -122.4477},
    {"name": "The Castro", "latitude": 37.7628, "longitude": -122.4350},
    {"name": "Mission District", "latitude": 37.7599, "longitude": -122.4148},
    {"name": "Haight-Ashbury", "latitude": 37.7690, "longitude": -122.4460},
    {"name": "Marin Headlands", "latitude": 37.8266, "longitude": -122.4993},
]
# ランドマーク一覧をPandas DataFrameに変換したもの
landmarks_df = pd.DataFrame(landmarks)

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Animation of Slider and Map", page_icon=":cinema:", layout="wide")
    st.title("Animation of Slider and Map")

# アニメーションする。実装パターンその1
def animation_impl1(sleep_time):
    # コンポーネントごとにst.empty()でプレースホルダを割り当てる
    placeholder1 = st.empty() # スライダー
    placeholder2 = st.empty() # 地図

    # sleep_time秒ごとに表示を更新。0-23時までアニメーションさせる
    for hour in range(24):
        # スライダーを表示
        # 指定された時刻をdatetime型に変換
        value = datetime.datetime(2024, 6, 3, 0, 0, 0, 0)
        value += datetime.timedelta(hours=hour)
        # st.sliderで[dt_start, dt_end]の範囲内で動くスライダーを表示する。プレースホルダに割り当てるためにplaceholder.sliderを使う
        placeholder1.slider("Current Time", dt_start, dt_end, value, format=slider_format)

        # 地図の表示
        # landmarks_dfにcolor列を追加。デフォルトは青色で、指定された時刻に対応するランドマークは赤色にする
        landmarks_df["color"] = "#0044ff"
        landmarks_df.loc[hour, "color"] = "#ff2222"
        # st.mapで表示する。プレースホルダに割り当てるためにplaceholder.mapを使う
        placeholder2.map(landmarks_df, latitude="latitude", longitude="longitude", color="color")

        # sleep_time秒待機
        time.sleep(sleep_time)

# アニメーションする。実装パターンその2
def animation_impl2(sleep_time):
    # あるプレースホルダのコンテナ内に更新するものを詰め込む
    placeholder = st.empty()
    for hour in range(24):
        with placeholder.container():
            # スライダーを表示
            # 指定された時刻をdatetime型に変換
            value = datetime.datetime(2024, 6, 3, 0, 0, 0, 0)
            value += datetime.timedelta(hours=hour)
            # st.sliderで[dt_start, dt_end]の範囲内で動くスライダーを表示する。with句でコンテナを指定しているためそのまま使える
            st.slider("Current Time", dt_start, dt_end, value, format=slider_format)

            # 地図の表示
            # landmarks_dfにcolor列を追加。デフォルトは青色で、指定された時刻に対応するランドマークは赤色にする
            landmarks_df["color"] = "#0044ff"
            landmarks_df.loc[hour, "color"] = "#ff2222"
            # st.mapで表示する。with句でコンテナを指定しているためそのまま使える
            st.map(landmarks_df, latitude="latitude", longitude="longitude", color="color")

            # sleep_time秒待機
            time.sleep(sleep_time)

# Main function
def main():
    # Initialize Streamlit
    init()

    # Implementation 1
    # animation_impl1(5)

    # Implementation 2
    animation_impl2(5)

if __name__ == '__main__':
    main()
