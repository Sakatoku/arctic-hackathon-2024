# osm_poi.py
# OpenStreetMapに登録されているPOIを取得するサンプル

"""
This script retrieves Points of Interest (POI) from OpenStreetMap using the Overpass API and displays them on a map using Streamlit and Folium.

The script performs the following steps:
1. Imports the necessary libraries: streamlit, folium, overpy, pandas, and pickle.
2. Defines the default area, latitude, and longitude.
3. Initializes Streamlit and sets the page configuration.
4. Defines functions to query restaurants and tourism spots in the target area using the Overpass API.
5. Defines a function to convert the Overpass API result to a DataFrame.
6. Defines functions to extract major restaurants and tourism spots based on metadata input.
7. Defines functions to build popup content for restaurants and tourism spots.
8. Defines a function to create a map and add markers for restaurants and tourism spots.
9. Defines a function to display the map using Streamlit and Folium.
10. Defines a function to serialize a DataFrame to a Pickle file.
11. Defines the main function that orchestrates the execution of the script.
12. Calls the main function if the script is executed directly.

To use this script, you need to have the necessary libraries installed and provide a target area. The script will query the Overpass API for restaurants and tourism spots in the target area, convert the results to DataFrames, extract major spots based on metadata input, create a map, and display it using Streamlit and Folium. You can also download the DataFrames as Pickle files.

Note: This script assumes that you have a valid Overpass API endpoint and the necessary API credentials.

Author: Akira Sakatoku
Date: 2024-05-13
"""

# Streamlit: https://www.streamlit.io/
import streamlit as st

# streamlit-folium: Folium wrapper for Streamlit
import folium
from streamlit_folium import st_folium

# OpenStreetMap Overpass API Python Wrapper
# pip install overpy
import overpy

# General libraries
import pandas as pd
import pickle

# Target area
default_area = "San Francisco"

# Default latitude/longitude
default_latitude = 37.77493
default_longitude = -122.41942

# Initialize Streamlit
def init():
    st.set_page_config(page_title="OSM POI", page_icon=":earth_americas:", layout="wide")
    st.title("OpenStreetMap POI")

# Query restaurants in target area
@st.cache_data
def query_restaurants(_api, area=default_area):
    restaurant_query_restaurant = f"area[\"name\"~\"{area}\"]; node(area)[\"amenity\"=\"restaurant\"]; out;"
    result = _api.query(restaurant_query_restaurant)
    return result

# Query tourism spots in target area
@st.cache_data
def query_tourism_spots(_api, area=default_area):
    restaurant_query_tourism = f"area[\"name\"~\"{area}\"]; node(area)[\"tourism\"]; out;"
    result = _api.query(restaurant_query_tourism)
    return result

# Convert Overpass API result to DataFrame
# latitude/longitudeはデフォルトでカラムに追加するため、columnsに指定しないこと
def convert_to_dataframe(result, columns=[]):
    df_columns = columns + ["latitude", "longitude"]
    df = pd.DataFrame(columns=df_columns, index=range(len(result.get_nodes())))
    for index, node in enumerate(result.get_nodes()):
        row = [node.tags.get(column, None) for column in columns]
        row += [node.lat, node.lon]
        df.iloc[index, :] = row
    return df

# メタデータの入力具合からメジャーなスポットを抽出する：restaurants
def extract_major_restaurants(df):
    # "cuisine", "opening_hours", "website"のすべてが入力されていることを抽出条件にする
    major_restaurants = df[df["cuisine"].notna() & df["opening_hours"].notna() & df["website"].notna()]
    return major_restaurants

# メタデータの入力具合からメジャーなスポットを抽出する：tourism spots
def extract_major_tourism_spots(df):
    # "website", "wikipedia"のいずれかが入力されていることを抽出条件にする
    tourism_spots = df[df["website"].notna() | df["wikipedia"].notna()]
    return tourism_spots

# Build popup content for restaurants
def build_restaurant_popup(row):
    popup = f"<b>{row['name']}</b>"
    if row["cuisine"] is not None:
        popup += f"<br>Cuisine: {row['cuisine']}"
    if row["opening_hours"] is not None:
        popup += f"<br>Opening Hours: {row['opening_hours']}"
    if row["website"] is not None:
        popup += f"<br>Website: <a href='{row['website']}' target='_blank'>{row['website']}</a>"
    return popup

# Build popup content for tourism spots
def build_tourism_spot_popup(row):
    popup = f"<b>{row['name']}</b>"
    if row["category"] is not None:
        popup += f"<br>Category: {row['category']}"
    if row["information"] is not None:
        popup += f"<br>Information: {row['information']}"
    if row["artwork_type"] is not None:
        popup += f"<br>Artwork Type: {row['artwork_type']}"
    if row["opening_hours"] is not None:
        popup += f"<br>Opening Hours: {row['opening_hours']}"
    if row["website"] is not None:
        popup += f"<br>Website: <a href='{row['website']}' target='_blank'>{row['website']}</a>"
    if row["wikipedia"] is not None:
        popup += f"<br>Wikipedia: <a href='{row['wikipedia']}' target='_blank'>{row['wikipedia']}</a>"
    return popup

# Create a map
@st.cache_resource
def create_map(df_restaurants, df_tourism_spots, center=(default_latitude, default_longitude), zoom=11):
    # Create map instance if it does not exist
    if 'map' not in st.session_state or st.session_state.map is None:
        new_map = folium.Map(
            location=center,
            tiles="cartodbpositron",
            zoom_start=zoom
        )

        # Add restaurants to the map
        for _, row in df_restaurants.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=build_restaurant_popup(row),
                icon=folium.Icon(color="green", icon="cutlery")
            ).add_to(new_map)

        # Add tourism spots to the map
        for _, row in df_tourism_spots.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=build_tourism_spot_popup(row),
                icon=folium.Icon(color="blue", icon="info-sign")
            ).add_to(new_map)

        st.session_state.map = new_map

    return st.session_state.map

# Display a map
@st.experimental_fragment
def display_map(map):
    st_folium(map, use_container_width=True, height=800)

# Serialize a DataFrame to a Pickle file
def serialize(df):
    serialized_bytes = pickle.dumps(df, protocol=4)
    return serialized_bytes

# Main function
def main():
    # Initialize Streamlit
    init()

    # Create Overpass API object
    api = overpy.Overpass()

    # Query restaurants in target area
    result = query_restaurants(api)

    # Convert Overpass API result to DataFrame
    df_restaurants = convert_to_dataframe(result, columns=["amenity", "name", "cuisine", "opening_hours", "website", "capacity", "internet_access", "wikidata"])
    # 後で結合しやすいようにカラム名を変更する：amenity -> category
    df_restaurants.rename(columns={"amenity": "category"}, inplace=True)
    st.dataframe(df_restaurants)

    # Query tourism spots in target area
    result = query_tourism_spots(api)

    # Convert Overpass API result to DataFrame
    df_tourism_spots = convert_to_dataframe(result, columns=["tourism", "name", "information", "artwork_type", "opening_hours", "website", "wikipedia", "wikidata"])
    # 後で結合しやすいようにカラム名を変更する：tourism -> category
    df_tourism_spots.rename(columns={"tourism": "category"}, inplace=True)
    st.dataframe(df_tourism_spots)

    # メジャーなものを抜き出す
    df_restaurants = extract_major_restaurants(df_restaurants)
    df_tourism_spots = extract_major_tourism_spots(df_tourism_spots)
    # st.dataframe(df_restaurants)
    # st.dataframe(df_tourism_spots)

    # Create a map and display it
    # map = create_map(df_restaurants, df_tourism_spots)
    # display_map(map)

    # Download DataFrames as Pickle files
    st.download_button(
        label="Download restaurants as Pickle",
        data=serialize(df_restaurants),
        file_name="restaurants.pkl",
        mime="application/octet-stream",
    )
    st.download_button(
        label="Download tourism spots as Pickle",
        data=serialize(df_tourism_spots),
        file_name="tourism_spots.pkl",
        mime="application/octet-stream",
    )

if __name__ == '__main__':
    main()
