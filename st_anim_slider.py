# st_anim_slider.py
# Streamlitのスライダーをアニメーションさせるサンプルプログラム

import streamlit as st
import datetime
import time

# 日時をパースする
def datetime_parse(date_str: str) -> datetime:
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

print("rerun")

placeholder1 = st.empty() # スライダー
placeholder2 = st.empty() # アクティビティ

# 開始時間と終了時間を取得する
dt_start = datetime_parse("2022-01-01T09:00:00Z")
dt_end = datetime_parse("2022-01-02T12:00:00Z")
interval_hour = (dt_end - dt_start).total_seconds() // 3600
if interval_hour == 0:
    interval_hour = 1

# アニメーションの更新間隔を設定する。すべてのアクティビティを120秒で表示する
sleep_time = 120 // interval_hour
if sleep_time < 1:
    sleep_time = 1
if sleep_time > 3:
    sleep_time = 3

# sleep_time秒ごとに表示を更新。ループアニメーションさせる
if "cursor" not in st.session_state:
    print("initialize cursor")
    st.session_state.cursor = 0
if "loop_count" not in st.session_state:
    print("initialize loop_count")
    st.session_state.loop_count = 0
print(st.session_state.cursor, st.session_state.loop_count, interval_hour, sleep_time)

activities = [
    "2022-01-01T09:00:00Z",
    "2022-01-01T13:00:00Z",
    "2022-01-01T15:00:00Z",
    "2022-01-01T19:00:00Z",
    "2022-01-01T20:00:00Z",
    "2022-01-02T08:00:00Z",
    "2022-01-02T09:00:00Z",
    "2022-01-02T12:00:00Z"
]

def update_cursor():
    # pass
    keys = st.session_state.keys()
    target_index = -1
    for key in keys:
        if key.startswith("slider:"):
            # キー名から値を取得
            loop_count = int(key.split(":")[1])
            if target_index < loop_count:
                target_index = loop_count
                value = st.session_state[key]
    st.session_state.cursor = (value - dt_start).total_seconds() // 3600
    print("update cursor: ", st.session_state.cursor)

print("enter loop")
while True:
    print("loop: ", st.session_state.loop_count, st.session_state.cursor)
    # スライダーを表示
    # 指定された時刻をdatetime型に変換
    dt_cur = dt_start + datetime.timedelta(hours=st.session_state.cursor)
    tmp = dt_cur
    # st.sliderで[dt_start, dt_end]の範囲内で動くスライダーを表示する。プレースホルダに割り当てるためにplaceholder.sliderを使う
    dt_cur = placeholder1.slider("Schedule", dt_start, dt_end, dt_cur, format="DD/HH", on_change=update_cursor, key=f"slider:{st.session_state.loop_count}")
    print(tmp, dt_cur)

    # 指定された時刻に該当するアクティビティを取得
    activity = activities[0]
    activity_index = 0
    for tmp_id, tmp_activity in enumerate(activities):
        dt_activity_start = datetime_parse(tmp_activity)
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
    # アクティビティを表示
    with placeholder2.container():
        st.write(f"Activity: {activity}")

    # sleep_time秒待機
    time.sleep(sleep_time)
    # ループ変数を更新
    # st.session_state.cursor = (dt_cur - dt_start).total_seconds() // 3600
    st.session_state.cursor = (st.session_state.cursor + 1) % (interval_hour + 1)
    st.session_state.loop_count += 1
    print("loop end: ", st.session_state.loop_count, st.session_state.cursor)
