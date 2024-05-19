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
    st.set_page_config(page_title="SakArctic Travel Agency", page_icon=":airplane_departure:", layout="wide")
    # st.title("Arctic Tourism Guide")
    st.image("resources/imgs/logo.png", width=1000)

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

# Unite two dataframes
def unite_df(restaulants_df, tour_df):
    columns = ["type", "name", "category", "website", "latitude", "longitude", "summary", "visit_time"]
    rows = []

    # restaulants_dfを1行ずつ処理して、rowsに追加する
    for i in range(len(restaulants_df)):
        type = "meal"
        name = restaulants_df.iloc[i]["NAME"]
        category = restaulants_df.iloc[i]["CUISINE"]
        website = restaulants_df.iloc[i]["WEBSITE"]
        latitude = restaulants_df.iloc[i]["LATITUDE"]
        longitude = restaulants_df.iloc[i]["LONGITUDE"]
        summary = restaulants_df.iloc[i]["WEB_SUMMARY"]
        visit_time = detetime_str_normalization(restaulants_df.iloc[i]["VISIT_TIME"])
        rows.append(pd.Series([type, name, category, website, latitude, longitude, summary, visit_time], index=columns))

    # tour_dfを1行ずつ処理して、rowsに追加する
    for i in range(len(tour_df)):
        type = "tour"
        name = tour_df.iloc[i]["NAME"]
        category = tour_df.iloc[i]["CATEGORY"]
        website = tour_df.iloc[i]["WEBSITE"]
        latitude = tour_df.iloc[i]["LATITUDE"]
        longitude = tour_df.iloc[i]["LONGITUDE"]
        summary = tour_df.iloc[i]["WEB_SUMMARY"]
        visit_time = detetime_str_normalization(tour_df.iloc[i]["VISIT_TIME"])
        rows.append(pd.Series([type, name, category, website, latitude, longitude, summary, visit_time], index=columns))

    # rowsをDataFrameに変換して、visit_timeでソートする
    df = pd.DataFrame(rows)
    df = df.sort_values('visit_time', ignore_index=True)
    return df

# 深夜にダミーアクティビティを追加する
def add_dummy_activities(activities_df):
    columns = ["type", "name", "category", "website", "latitude", "longitude", "summary", "visit_time"]
    rows = []

    # 日付が変わるタイミングを探索する
    for i in range(len(activities_df) - 1):
        dt1 = datetime_parse(activities_df.iloc[i]["visit_time"])
        dt2 = datetime_parse(activities_df.iloc[i + 1]["visit_time"])

        # 日付が変わるタイミングで、4時間以上の間隔がある場合にダミーアクティビティを追加する
        if dt1.day < dt2.day and (dt2 - dt1).total_seconds() > 3600 * 4:
            # ダミーアクティビティを追加する
            type = "stay"
            name = "Your Hotel"
            category = "hotel"
            website = ""
            latitude = 0
            longitude = 0
            summary = "Please have a restful and peaceful sleep."
            visit_time = (dt1 + datetime.timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
            rows.append(pd.Series([type, name, category, website, latitude, longitude, summary, visit_time], index=columns))

    # 既存のアクティビティとダミーアクティビティを結合する
    df = pd.concat([activities_df, pd.DataFrame(rows)], ignore_index=True)
    df = df.sort_values('visit_time', ignore_index=True)
    return df

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
    # ダミーアクティビティの場合は画像を生成しないであらかじめ用意した画像を返す
    if activity["type"] == "stay":
        return "resource/imgs/midnight.jpg"

    # Replicate APIへの入力
    prompt = generate_prompt(activity)
    input = {
        "prompt": prompt
    }

    # Replicate APIを呼び出して画像を生成する
    try:
        client = replicate.Client(api_token=os.environ["REPLICATE_API_TOKEN"])
        output = client.run(
            "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
            input=input
        )
        return output[0]
    except replicate.exceptions.ModelError as e:
        print(f"Error: {e}")
        return "resource/imgs/error.jpg"

# スライダーのコールバック
def update_slider():
    # キーを探索する
    keys = st.session_state.keys()
    newest_key_index = -1
    for key in keys:
        if key.startswith("slider:"):
            key_index = int(key.split(":")[1])
            if newest_key_index < key_index:
                newest_key_index = key_index
                dt_cur = st.session_state[key]
    # カーソルを更新する
    st.session_state.cursor = (dt_cur - st.session_state.dt_start).total_seconds() // 3600

# スライダーとアクティビティを連動でアニメーションさせる
def animation_sliders():
    # アクティビティの情報を取得する
    activities = st.session_state.activities

    # コンポーネントごとにst.empty()でプレースホルダを割り当てる
    placeholder1 = st.empty() # スライダー
    placeholder2 = st.empty() # アクティビティ

    # 開始時間と終了時間を取得する
    dt_start = datetime_parse(activities[0]["datetime"])
    dt_end = datetime_parse(activities[-1]["datetime"])
    st.session_state.dt_start = dt_start
    st.session_state.dt_end = dt_end
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
    if "cursor" not in st.session_state:
        st.session_state.cursor = 0
    if "loop_count" not in st.session_state:
        st.session_state.loop_count = 0
    map_disabled = True
    while True:
        # スライダーを表示
        # 指定された時刻をdatetime型に変換
        dt_cur = dt_start + datetime.timedelta(hours=st.session_state.cursor)
        # st.sliderで[dt_start, dt_end]の範囲内で動くスライダーを表示する。プレースホルダに割り当てるためにplaceholder.sliderを使う
        placeholder1.slider("Schedule", dt_start, dt_end, dt_cur, format="MM/DD hh A", on_change=update_slider, key=f"slider:{st.session_state.loop_count}")

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
        if map_disabled:
            map = create_map(activities)
            display_map(map)
            map_disabled = False

        # sleep_time秒待機
        time.sleep(sleep_time)
        # ループ変数を更新。深夜ならスキップする
        cursor_hop = 1
        if activity["type"] == "stay":
            st.session_state.cursor = (st.session_state.cursor + cursor_hop) % (interval_hour + 1)
        st.session_state.loop_count += 1

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
def generate_description(data):
    type = data["type"]
    name = data["location"]["name"]
    category = data["category"]
    summary = data["summary"]
    visit_time = data["datetime"]
    if type == "stay":
        catchphrase = "Good night."
        description = summary
        return f"{{\"catchphrase\": \"{catchphrase}\", \"description\": \"{description}\"}}"
    elif type == "meal":
        prompt = f'Generate a catchphrase and detailed description for this restaurant. Restaurant information is follows: {{ "name": "{name}", "category": "{category}", "visit_time": "{visit_time}", "web_summary": "{summary}" }} Your output should be formatted as follows: {{ "catchphrase": "...", "description": "..." }}'
    else:
        prompt = f'Generate a catchphrase and detailed description for this sightseeing activity. Sightseeing activity information is follows: {{ "name": "{name}", "category": "{category}", "visit_time": "{visit_time}", "web_summary": "{summary}" }} Your output should be formatted as follows: {{ "catchphrase": "...", "description": "..." }}'
    prompt = escape_string_for_sql(prompt)

    # Snowflake Coretex APIを呼び出してテキストを生成する
    try:
        session = connect_snowflake()
        selected_model = "snowflake-arctic"
        cmd = f"select snowflake.cortex.complete('{selected_model}', [{{'role': 'user', 'content': '{prompt}'}}], {{'temperature': 0.3}}) as RESPONSE"
        df_response = session.sql(cmd).collect()
        json_response = json.loads(df_response[0]["RESPONSE"])
        return json_response['choices'][0]['messages']
    except Exception as e:
        print(f"Error: {e}")
        return None

# 日時文字列を正規化する
def detetime_str_normalization(datetime_str: str):
    # 1/1 09:00 -> 2022-01-01T12:00:00Z
    # datetimeでパースしてから、UTCに変換する
    dt = datetime.datetime.strptime(datetime_str, '%m/%d %H:%M')
    dt = dt.replace(year=2024)
    # Do not convert to UTC
    # dt = dt.astimezone(datetime.timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# アクティビティの情報を生成する
@st.cache_data
def generate_activities(restaurants_filename: str, tour_filename: str) -> list:
    # セッション変数に既にあればそれを返す
    if "activities" in st.session_state:
        return st.session_state.activities

    # ファイルからアクティビティの情報を読み込む
    restaurants_df = pd.read_csv(restaurants_filename)
    tour_df = pd.read_csv(tour_filename)
    all_df = unite_df(restaurants_df, tour_df)
    all_df = add_dummy_activities(all_df)

    # データ生成の進捗表示
    placeholder1 = st.empty()
    with placeholder1.container():
        header_str = "Generating plans."
        st.subheader(header_str)
        st.progress(0.0)

    # all_dfにアクティビティの情報が格納されている。1行づつ処理していく
    activities = []
    for index, row in all_df.iterrows():
        # データをdictに整理する
        activity = dict()
        activity["type"] = row['type']
        activity["category"] = row['category']
        activity["url"] = row['website']
        activity["summary"] = row['summary']
        activity["datetime"] = row['visit_time']
        activity["location"] = {
            "name": row['name'],
            "latitude": row['latitude'],
            "longitude": row['longitude']
        }

        # アクティビティの情報からキャッチフレーズと詳細な説明を生成する
        response = generate_description(activity)
        if response is None:
            continue

        try:
            # 生成した結果をJSONに変換する
            description = json.loads(response)

            # アクティビティの情報を追加する            
            activity["title"] = description["catchphrase"]
            activity["description"] = description["description"]

            # リストに追加する
            activities.append(activity)
        except:
            continue

        # 進捗を更新する
        with placeholder1.container():
            header_str = "Generating plans."
            for _ in range(index + 1):
                header_str += "."
            st.subheader(header_str)
            st.progress((index + 1) / len(all_df))

    # セッション変数にアクティビティの情報を保存する
    st.session_state.activities = activities

    # 進捗を完了にする
    placeholder1.empty()

    # 生成したアクティビティの情報を表示する
    with st.expander("Generated Activities"):
        st.write(st.session_state.activities)

    return st.session_state.activities

# Main function
def main():
    # Streamlitの初期化
    init()

    # アクティビティの情報を生成する
    st.session_state.activities = generate_activities("temp/restaurants_result_df.csv", "temp/tour_result_df.csv")

    # すべてのアクティビティを表示
    animation_sliders()

if __name__ == "__main__":
    main()
