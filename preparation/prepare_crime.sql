use role sysadmin;
use database tourism;

CREATE OR REPLACE TABLE POPULATIONS_STATISTICS AS
SELECT
    cs.*,
    zip.*,
FROM (
    SELECT
        geo.geo_name AS zipcode,
        SUM(ts.value) AS sum_crime
    FROM crime_statistics.cybersyn.urban_crime_timeseries AS ts
    JOIN crime_statistics.cybersyn.geography_index AS geo
        ON ts.geo_id = geo.geo_id
    WHERE ts.variable_name = 'Daily count of incidents, all incidents'
    GROUP BY geo.geo_name
) AS cs
JOIN US_ZIP_CODE_METADATA__POPULATIONS_GEO_CENTROID_LATLNG_CITY_NAMES_STATE_DMA_DEMOGRAPHICS.ZIP_DEMOGRAPHICS.ZIP_CODE_METADATA AS zip
    ON cs.zipcode = zip.zip
WHERE zip.city = 'San Francisco';


CREATE OR REPLACE TABLE cl_restaurants_finalized as 
SELECT 
    a.name as name,
    a.cuisines as cuisines,
    a.cuisine as cuisine,
    a.website as website,
    a.latitude as latitude,
    a.longitude as longitude,
    a.open_time as open_time,
    a.close_time as close_time,
    a.web_summary as web_summary,
    b.sum_crime as sum_crime,
FROM 
    (
        SELECT 
            *, 
            ST_POINT(longitude, latitude) AS p 
        FROM tourism.public.cl_restaurants_finalized
    ) a
JOIN 
    (
        SELECT 
            *,
            ST_POINT(longitude, latitude) AS p 
        FROM POPULATIONS_STATISTICS
    ) b
QUALIFY 
    ROW_NUMBER() OVER (PARTITION BY a.name ORDER BY ST_DISTANCE(a.p, b.p)) = 1;


CREATE OR REPLACE TABLE tourism_spots_finalized as 
SELECT 
    a.category as category,
    a.name as name,
    a.information as information,
    a.artwork_type as artwork_type,
    a.opening_hours as opening_hours,
    a.website as website,
    a.wikipedia as wikipedia,
    a.wikidata as wikidata,
    a.latitude as latitude,
    a.longitude as longitude,
    a.web_summary as web_summary,
    b.sum_crime as sum_crime,
FROM 
    (
        SELECT 
            *, 
            ST_POINT(longitude, latitude) AS p 
        FROM tourism.public.tourism_spots_finalized
    ) a
JOIN 
    (
        SELECT 
            *,
            ST_POINT(longitude, latitude) AS p 
        FROM POPULATIONS_STATISTICS
    ) b
QUALIFY 
    ROW_NUMBER() OVER (PARTITION BY a.name ORDER BY ST_DISTANCE(a.p, b.p)) = 1;