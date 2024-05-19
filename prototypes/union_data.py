# union_data.py
# union two dataframes and sort by visit_time

import streamlit as st
import pandas as pd
import datetime

filename1 = "temp/restaurants_result_df.csv"
filename2 = "temp/tour_result_df.csv"
df1 = pd.read_csv(filename1)
df2 = pd.read_csv(filename2)
st.write(df1)
st.write(df2)

# 日時文字列を正規化する
def detetime_str_normalization(datetime_str: str):
    # 1/1 09:00 -> 2022-01-01T12:00:00Z
    # datetimeでパースしてから、UTCに変換する
    dt = datetime.datetime.strptime(datetime_str, '%m/%d %H:%M')
    dt = dt.replace(year=2024)
    # dt = dt.astimezone(datetime.timezone.utc)
    return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

# Unite two dataframes
def unite_df(restaulants_df, tour_df):
    columns = ["type", "name", "category", "website", "latitude", "longitude", "summary", "visit_time"]
    rows = []
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
    df = pd.DataFrame(rows)
    df = df.sort_values('visit_time', ignore_index=True)
    return df

df = unite_df(df1, df2)
st.write(df)
