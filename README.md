# SAKATALK Travel Agency: A concept application for Snowflake Arctic Hackathon

## About

This application serves as a trip plan generator. It interacts with users through a chat interface, gathering their preferences and requirements, and then creates a customized trip plan based on the collected information.  
We create this application for [THE FUTURE OF AI IS OPEN](https://arctic-streamlit-hackathon.devpost.com/).  

## Our project story

Japan is often referred to as an island nation, where many people are deeply connected to their hometowns and not everyone participates in international activities.  
However, post-COVID-19, an increasing number of Japanese are eager to explore the world, especially engineers fascinated by the potential of Data Cloud.  

So, how can we, who might not be seasoned travelers, enjoy our journeys to the fullest?  

We have developed an innovative application that leverages diverse datasets from the Snowflake Marketplace and the Internet, utilizing Large Language Models (LLMs) to craft personalized travel plans tailored to a wide array of preferences and needs.
By using this application, you can enjoy comfortable, safe, and enriching travels.  
Join us in exploring the world with our cutting-edge technology. We look forward to meeting you at the Snowflake Data Cloud Summit 2024!  

日本が島国であるということは、多くの日本人が口にします。多くの日本人は自身の出身地に根付いた暮らしをしており、すべての人が国際的に活動しているわけではありません。  
しかし、COVID-19の危機を乗り越えて、世界に旅立つ日本人が増えてきました。それがデータクラウドの可能性に魅了されたエンジニアたちであれば、なおさら。  

そこで、旅慣れていない我々が旅を楽しむための助けになるものは何でしょうか？  

私たちは、Snowflake Marketplaceやインターネット上に存在する多様なデータセットを活用し、LLM(大規模言語モデル)を通じて、多様なニーズに対応できるパーソライズされた旅行プランを提案するアプリケーションを実現しました。  
このアプリケーションを用いることで、快適で安全、そして実りのある旅を楽しめることでしょう。  
私たちの最新のテクノロジーと一緒に世界を探検してください。Snowflake Data Cloud Summit 2024で皆様にお会いできることを楽しみにしています！  

![Concept Art](https://github.com/Sakatoku/arctic-hackathon-2024/blob/main/resources/imgs/concept-art.jpg?raw=true)

## How does this application work

- Phase 1: Data preparation
- Phase 2: Hearing user preferences
- Phase 3: Generate plan and visualize it

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
