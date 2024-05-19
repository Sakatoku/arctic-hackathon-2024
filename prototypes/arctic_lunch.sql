-- ロールの切り替えとテストクエリ
USE ROLE CORTEX_USER_ROLE;
SELECT * FROM TEST_DATABASE.PUBLIC.SF_RESTAURANTS LIMIT 10;
SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', 'Hello.');

-- Snowflake Arkticで営業時間を正規化する
create or replace table cl_restaurants as
with target as (
    select *
    from test_database.public.sf_restaurants
    where
        cuisine is not null
        and opening_hours is not null
        and website is not null
),
mid1 as (
    select *, 
        snowflake.cortex.complete(
            'snowflake-arctic',
            concat(
                'Description between <business_hour>tag is business hours of a store.\n',
                'Typically, business hours are described in the format (opening_time)-(closing_time).\n',
                'It is sometimes accompanied by the day of the week.\n',
                'Description between <weekday>tag is designated day of the week.\n',
                'Please convert business hours of designate day of the week the following format:',
                '<open>(opening_time)</open><close>(closing_time)</close>\n',
                '<business_hours>' || opening_hours || '</business_hours>\n',
                '<weekday>Any</weekday>\n'
            )
        ) as response,
    from target
),
mid2 as (
    select *,
        regexp_substr(response, '<open>(\\d\\d:\\d\\d)</open>', 1, 1, 'e', 1) as open_time_frag,
        regexp_substr(response, '<close>(\\d\\d:\\d\\d)</close>', 1, 1, 'e', 1) as close_time_frag,
    from mid1
),
mid3 as (
    select *,
        iff(open_time_frag = '24:00', '00:00', open_time_frag) as open_time_frag2,
        iff(close_time_frag = '24:00', '00:00', close_time_frag) as close_time_frag2,
    from mid2
),
mid4 as (
    select *,
        (open_time_frag2 || ':00')::time as open_time,
        (close_time_frag2 || ':00')::time as close_time,
    from mid3
),
result as (
    select category, name, cuisine, website, latitude, longitude, open_time, close_time
    from mid4
    where
        open_time is not null
        and close_time is not null
)
select * from result;

-- Check the created table
SELECT * FROM cl_restaurants;
