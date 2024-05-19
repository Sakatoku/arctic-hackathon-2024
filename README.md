# SAKATALK Travel Agency: A concept app for Snowflake Arctic Hackathon

## About

This application serves as a trip plan generator. It interacts with users through a chat interface, gathering their preferences and requirements, and then creates a customized trip plan based on the collected information.  
We create this application for [THE FUTURE OF AI IS OPEN](https://arctic-streamlit-hackathon.devpost.com/).  

## Our project story

日本は島国である、とよく我々日本人は言います。多くの日本人が自身の出身地に深く根差した暮らしをしていて、誰もがグローバルに活動をしている訳ではありません。  
しかしながら、COVID-19の悲劇を乗り越えて世界に旅立つ日本人が増えてきました。それがデータクラウドの世界観に魅了されたエンジニアであるのであれば、なおさら。  
旅慣れぬ我々がどのように旅を楽しむための助けになるものはなんでしょうか？  
我々はSnowflakeのデータクラウドやオープンデータに存在する多様なデータセットを、LLMを通じて活用することで、多様なニーズにパーソナライズされた旅行プランを提案するアプリケーションを実現しました。  
快適、安全、そして実りある旅行をお楽しみください。Data Cloud Summit 2024で会いましょう！  

## Demo

## Requirements

requirements.txtを参照。

```txt:requirements.txt
streamlit
streamlit-folium
snowflake-connector-python
snowflake-snowpark-python
snowflake-ml-python[all]
pandas
replicate
beautifulsoup4
```

## Usage

### On local environments

First, create ```secrets.toml``` file.

```toml:.streamlit/secrets.toml
[Snowflake]
user = "USER"
password = "PASSWORD"
account = "ACCOUNT-IDENTIFIER"
role = "ROLE"
warehouse = "WAREHOUSE"

[Replicate]
apikey = "r8_****"
```

Next, type the following command:

```sh
streamlit run demo/home.py
```

### On Streamlit Cloud

Create app with ```demo/home.py``` for ```Main file path``` parameter, and input Secrets as following format.

```toml:.streamlit/secrets.toml
[Snowflake]
user = "USER"
password = "PASSWORD"
account = "ACCOUNT-IDENTIFIER"
role = "ROLE"
warehouse = "WAREHOUSE"

[Replicate]
apikey = "r8_****"
```

## Authors

- [Sakatoku](https://github.com/Sakatoku)
- [Toru Hiyama](https://github.com/THiyama)
- [hrk](https://github.com/hrk-mrks)
