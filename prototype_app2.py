# prototype_app2.py
# 観光推薦アプリのGUIのプロトタイプ

# Streamlit: https://www.streamlit.io/
import streamlit as st

# Snowflake and Snowpark
import snowflake.connector
import snowflake.snowpark as snowpark
import snowflake.cortex as cortex

# Replicate library
import replicate

# streamlit-folium: Folium wrapper for Streamlit
import folium
from streamlit_folium import st_folium

# general libraries
import pandas as pd
import json
import datetime
import time
import os

# 接続するSnowflake環境を指定する
ENVIRONMENT = "SnowflakeProd"

# Default latitude/longitude
default_latitude = 37.77493
default_longitude = -122.41942

# Initialize Streamlit
def init():
    st.set_page_config(page_title="Arctic Tourism Guide", page_icon=":airplane_departure:", layout="wide")
    st.title("Arctic Tourism Guide")

    # ReplicateとOpenAIのAPIキーを環境変数に設定する
    os.environ["REPLICATE_API_TOKEN"] = st.secrets["Replicate"]["apikey"]

# ローカルPython環境からSnowflakeに接続するための関数
@st.cache_resource(ttl=7200)
def connect_snowflake():
    # Snowflakeに接続する
    # Snowflakeの接続情報はStreamlitのシークレット(.streamlit/secret.toml)に保存しておく
    connection = snowflake.connector.connect(
        user=st.secrets[ENVIRONMENT]["user"],
        password=st.secrets[ENVIRONMENT]["password"],
        account=st.secrets[ENVIRONMENT]["account"],
        role=st.secrets[ENVIRONMENT]["role"],
        warehouse=st.secrets[ENVIRONMENT]["warehouse"])

    # Snowparkセッションを作成する
    session = snowpark.Session.builder.configs({"connection": connection}).create()
    return session 

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
            interval_hour = (dt2 - dt1).total_seconds() // 3600
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
def animation_sliders(activities):
    # コンポーネントごとにst.empty()でプレースホルダを割り当てる
    placeholder1 = st.empty() # スライダー
    placeholder2 = st.empty() # アクティビティ

    # 開始時間と終了時間を取得する
    dt_start = datetime_parse(activities[0]["datetime"])
    dt_end = datetime_parse(activities[-1]["datetime"])
    # dt_startとdt_endの間に何時間あるかを計算する
    interval_hour = (dt_end - dt_start).total_seconds() // 3600
    if interval_hour == 0:
        interval_hour = 1

    # アニメーションの更新間隔を設定する。すべてのアクティビティを120秒で表示する
    sleep_time = 120 // interval_hour
    if sleep_time < 1:
        sleep_time = 1
    if sleep_time > 20:
        sleep_time = 20

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

# 文字列をエスケープする: SQL用
def escape_string_for_sql(s):
    return s.replace("'", "''")

# 文字列をエスケープする: JSON用
def escape_string_for_json(s):
    return s.replace('"', '\\"')

# Snowflakeからレストランデータを取得する
def get_restaurant_data_from_snowflake(name, cuisine):
    # Snowflakeに接続する
    session = connect_snowflake()
    # SQLを実行してデータを取得する
    name = escape_string_for_sql(name)
    cuisine = escape_string_for_sql(cuisine)
    df_sql = session.sql("SELECT * FROM TOURISM.PUBLIC.CL_RESTAURANTS_FINALIZED WHERE NAME = '{}' AND CUISINE = '{}' LIMIT 1".format(name, cuisine)).to_pandas()
    return df_sql

# キャッチフレーズと詳細な説明を生成する
def generate_description(data, visit_time):
    name = data['NAME'][0]
    cuisine = data['CUISINE'][0]
    summary = data['WEB_SUMMARY'][0]
    prompt = f'Generate a catchphrase and detailed description for this restaurant. Restaurant information is follows: {{ "name": "{name}", "cuisine": "{cuisine}", "visit_time": "{visit_time}", "web_summary": "{summary}" }} Your output should be formatted as follows: {{ "catchphrase": "...", "description": "..." }}'
    prompt = escape_string_for_sql(prompt)

    # Snowflake Coretex APIを呼び出してテキストを生成する
    session = connect_snowflake()
    selected_model = "snowflake-arctic"
    cmd = f"select snowflake.cortex.complete('{selected_model}', [{{'role': 'user', 'content': '{prompt}'}}], {{'temperature': 0.3}}) as RESPONSE"
    df_response = session.sql(cmd).collect()
    json_response = json.loads(df_response[0]["RESPONSE"])
    return json_response['choices'][0]['messages']

# 日時文字列を正規化する
def detetime_str_normalization(datetime_str: str):
    # 1/1 09:00 -> 2022-01-01T12:00:00Z
    # datetimeでパースしてから、UTCに変換する
    dt = datetime.datetime.strptime(datetime_str, '%m/%d %H:%M')
    dt = dt.replace(year=2024)
    dt = dt.astimezone(datetime.timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# アクティビティの情報を生成する
def generate_activities(filename: str) -> list:
    # ファイルからアクティビティの情報を読み込む
    restaurants_df = pd.read_csv(filename)

    # データ生成の進捗表示
    placeholder1 = st.empty()
    with placeholder1.container():
        header_str = "Generating plans."
        st.subheader(header_str)
        st.progress(0.0)

    # restaurant_dfに行先となるレストランの情報が格納されている。1行づつ処理していく
    activities = []
    for index, row in restaurants_df.iterrows():
        # name, cuisine, visit_timeを取得する
        name = row['NAME']
        cuisine = row['CUISINE']
        visit_time = row['VISIT_TIME']

        # Snowflakeからレストランデータを取得する
        restaurant_data = get_restaurant_data_from_snowflake(name, cuisine)

        # レストランデータからキャッチフレーズと詳細な説明を生成する
        response = generate_description(restaurant_data, visit_time)

        try:
            # 生成した結果をJSONに変換する
            description = json.loads(response)
            
            # データをdictに整理する
            activity = dict()
            activity["type"] = "meal"
            activity["title"] = description["catchphrase"]
            activity["description"] = description["description"]
            activity["url"] = restaurant_data["WEBSITE"][0]
            activity["datetime"] = detetime_str_normalization(visit_time)
            activity["location"] = {
                "name": name,
                "latitude": restaurant_data["LATITUDE"][0],
                "longitude": restaurant_data["LONGITUDE"][0]
            }
            activities.append(activity)
        except Exception as e:
            continue

        # 進捗を更新する
        with placeholder1.container():
            header_str = "Generating plans."
            for _ in range(index + 1):
                header_str += "."
            st.subheader(header_str)
            st.progress((index + 1) / len(restaurants_df))

    # 進捗を完了にする
    placeholder1.empty()

    return activities

# Main function
def main():
    # Streamlitの初期化
    init()

    # アクティビティの情報を生成する
    activities = generate_activities("temp/restaurants_result_df.csv")

    # すべてのアクティビティを表示
    animation_sliders(activities)

if __name__ == "__main__":
    main()
