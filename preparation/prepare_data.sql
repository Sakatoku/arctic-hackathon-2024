use role sysadmin;
use database tourism;

// data cleansing
CREATE OR REPLACE TABLE cl_restaurants_finalized AS
SELECT 
    r.NAME,
    r.CUISINE AS CUISINES,
    TRIM(f.value, '"') AS CUISINE,
    r.WEBSITE,
    r.LATITUDE,
    r.LONGITUDE,
    r.OPEN_TIME,
    r.CLOSE_TIME,
    r.WEB_SUMMARY,
FROM 
    cl_restaurants_summarized r,
    LATERAL FLATTEN(INPUT => SPLIT(r.CUISINE, ';')) f
WHERE
    r.WEB_SUMMARY is not null;

CREATE OR REPLACE TABLE tourism_spots_finalized AS
SELECT * FROM tourism_spots_summarized
WHERE web_summary is not null;


// text embedding using cortex for web_summary
CREATE OR REPLACE TABLE tourism.public.cl_restaurants_finalized AS 
SELECT *, snowflake.cortex.EMBED_TEXT_768('snowflake-arctic-embed-m', web_summary) AS embeded_web_summary 
FROM tourism.public.cl_restaurants_finalized;

CREATE OR REPLACE TABLE tourism.public.tourism_spots_finalized AS 
SELECT *, snowflake.cortex.EMBED_TEXT_768('snowflake-arctic-embed-m', web_summary) AS embeded_web_summary 
FROM tourism.public.tourism_spots_finalized;
