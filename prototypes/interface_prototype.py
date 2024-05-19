# interface-prototype.py
# 観光推薦アプリのGUIのプロトタイプ

# Streamlit: https://www.streamlit.io/
import streamlit as st

# Replicate library
import replicate

# streamlit-folium: Folium wrapper for Streamlit
import folium
from streamlit_folium import st_folium

# general libraries
from PIL import Image
import json 
import datetime
import time
import os

# Default latitude/longitude
default_latitude = 37.77493
default_longitude = -122.41942

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Arctic Tourism Guide", page_icon=":airplane_departure:", layout="wide")
    st.title("Arctic Tourism Guide")

    # ReplicateとOpenAIのAPIキーを環境変数に設定する
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["Replicate"]["apikey"]

# JSONをファイルから読み込む
def read_json(filename: str) -> dict:
    with open(filename, "r", encoding="utf8") as f:
        json_obj = json.load(f)
    return json_obj

# Build popup content
def build_popup(item: dict) -> str:
    template = "<b>{}</b><br>{}<br>{}<br>{}<br>{}"
    popup = template.format(item["title"], item["location"]["name"], item["type"], item["description"], item["url"])
    return popup

# Create a map
@st.cache_resource
def create_map(activities: dict, center=(default_latitude, default_longitude), zoom=13):
    # Create map instance if it does not exist
    if "map" not in st.session_state or st.session_state.map is None:
        new_map = folium.Map(
            location=center,
            tiles="cartodbpositron",
            zoom_start=zoom
        )

        # Add restaurants to the map
        for item in activities:
            folium.Marker(
                location=[item["location"]["latitude"], item["location"]["longitude"]],
                popup=build_popup(item),
                icon=folium.Icon(color="green", icon="info-sign")
            ).add_to(new_map)

        st.session_state.map = new_map

    return st.session_state.map

# Display a map
@st.experimental_fragment
def display_map(map):
    st_folium(map, use_container_width=True, height=600)

# 日時をパースする
def datetime_parse(date_str: str) -> datetime:
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

# アクティビティを表示する
def display_activity(placeholder, activity: dict, next_activity: dict):
    with placeholder.container():
        # 画像を左側に、説明文を右側に表示する
        col_left, col_right = st.columns(2)

        # 開始時間と終了時間を取得する
        dt1 = datetime_parse(activity["datetime"])
        interval_hour = 24 - dt1.hour
        if next_activity is not None:
            dt2 = datetime_parse(next_activity["datetime"])
            interval_hour = dt2.hour - dt1.hour
        start_time_str = dt1.strftime("%I:00 %p")
        
        # 左側に画像を表示
        with col_left:
            image_url = activity["image"]
            st.image(image_url)

        # 右側に説明文を表示
        with col_right:
            st.subheader(activity["title"])
            st.markdown("at **{}**".format(activity["location"]["name"]))
            st.markdown("from **{}** ({} hours)".format(start_time_str, interval_hour))
            st.write(activity["description"])
            st.write("[{}]({})".format(activity["url"], activity["url"]))

# プロンプトを生成する
def generate_prompt(situations):
    type = situations["type"]
    title = situations["title"]
    spot_name = situations["location"]["name"]
    description = situations["description"]
    datetime = situations["datetime"]
    return f"""
    Create a photorealistic image of the following situations: {{ "type": {type}, "title": {title} , "spot_name": {spot_name}, "description": {description}, "datetime": {datetime} }}.
    """

# 画像を生成する
def generate_image(activity):
    # Replicate APIへの入力
    prompt = generate_prompt(activity)
    input = {
        "prompt": prompt
    }

    # Replicate APIを呼び出して画像を生成する
    client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])
    output = client.run(
        "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
        input=input
    )
    return output[0]

# スライダーとアクティビティを連動でアニメーションさせる
def animation_sliders(activities, sleep_time):
    # コンポーネントごとにst.empty()でプレースホルダを割り当てる
    placeholder1 = st.empty() # スライダー
    placeholder2 = st.empty() # アクティビティ

    # 開始時間と終了時間を取得する
    dt_start = datetime_parse(activities[0]["datetime"])
    dt_end = datetime_parse(activities[-1]["datetime"])
    # dt_startとdt_endの間に何時間あるかを計算する
    interval_hour = (dt_end - dt_start).seconds // 3600

    # sleep_time秒ごとに表示を更新。ループアニメーションさせる
    cursor = 0
    loop_count = 0
    while True:
        # スライダーを表示
        # 指定された時刻をdatetime型に変換
        dt_cur = dt_start + datetime.timedelta(hours=cursor)
        # st.sliderで[dt_start, dt_end]の範囲内で動くスライダーを表示する。プレースホルダに割り当てるためにplaceholder.sliderを使う
        dt_cur = placeholder1.slider("Schedule", dt_start, dt_end, dt_cur, format="MM/DD hh A", key=loop_count)

        # 指定された時刻に該当するアクティビティを取得
        activity = activities[0]
        activity_index = 0
        for tmp_id, tmp_activity in enumerate(activities):
            dt_activity_start = datetime_parse(tmp_activity["datetime"])
            # print(dt_cur, dt_activity_start)
            if dt_activity_start <= dt_cur:
                activity = tmp_activity
                activity_index = tmp_id
            else:
                break
        # 次のアクティビティを取得
        next_activity = None
        if activity_index < len(activities) - 1:
            next_activity = activities[activity_index + 1]
        # 画像がなければ画像を生成する
        if "image" not in activity:
            activities[activity_index]["image"] = generate_image(activity)
        # アクティビティを表示
        display_activity(placeholder2, activity, next_activity)

        # Create a map and display it
        if loop_count == 0:
            map = create_map(activities)
            display_map(map)

        # sleep_time秒待機
        time.sleep(sleep_time)
        # ループ変数を更新
        cursor = (cursor + 1) % (interval_hour + 1)
        loop_count += 1

# Main function
def main():
    # Streamlitの初期化
    init()

    # JSONファイルの読み込み
    json_obj = read_json("stub/dummy-input.json")

    # Create a map and display it
    # map = create_map(json_obj["activities"])
    # display_map(map)
    
    # すべてのアクティビティを表示
    animation_sliders(json_obj["activities"], 2)

if __name__ == "__main__":
    main()
