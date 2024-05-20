## Phase 1: Data preparation

### Get POI registered in OpenStreetMap
- Run the command below to start the application to extract restaurants and tourist attractions. 
```sh
streamlit run .\preparation\osm_poi.py
```
- 下記のPythonスクリプトで、pklファイルをCSVファイルに変換してください。
```python
base_filename = "filename"
df = pd.read_pickle(base_filename + ".pkl")
df.to_csv(base_filename + ".csv", index=False)
```
- Upload the CSV files to Snowflake with the names below. The "+Create" button at the top of Snowsight's navigation bar is convenient.🌝
    - restaurants.pkl -> tourism.public.cl_restaurants
    - tourism_spots.pkl -> tourism.public.tourism_spots

### Get web site information and Summarize this
- Prerequisite: `osm_poi.py` has been executed. The pkl files are loaded into Snowflake. 
- The below command extracts information from the WEBSITE stored in the table and summarizes it using Snowflake.Cortex's Summarize function. Make sure to run it from the top of the repository.
```sh
python .\preparation\collect_restaurants_information.py
```
- Execute the SQL file `prepare_data.sql` on Snowflake for data cleansing and preprocessing (vectorization).
- (optional) By acquiring the data below from Snowflake Marketplace and running the SQL file `prepare_crime.sql`, you will be able to obtain the annual number of crimes per zip code. Don't forget to grant appropriate permissions when acquiring data. If you have this data, you will be able to add the number of crimes as a weight for record extraction.
    - Cybersyn, Crime Statistics
    - Deep Sync, US Zip Code Metadata - Populations, Geo Centroid Lat/Lng, City Names, State, DMA, Demographics