# breadcrumb.py
# 見た目だけのパンくずリストを生成する

import streamlit as st

def show_breadcrumb():
    # HTML埋め込み
    css_code = """
    <style>
        .breadcrumb { display: inline-block; margin: 0; padding: 0; list-style: none; }
        .breadcrumb li { display: inline-block; margin: 0; padding: 0; }
        .breadcrumb li span { margin: 0; padding: 0.3em 1.3em 0.3em 1em; list-style: none; display: inline-block; border-radius: 15px; text-decoration: none; font-size: 0.9em; }
        .breadcrumb li:after { content: "\\025b6"; margin: 0 0.2em 0 0.5em; color: #c0c0c0; }
        .breadcrumb li:last-child:after { content: ""; }
        .active { color: #ffffff; background: #249edc; }
        .inactive { color: #ffffff; background: #c0c0c0; }
    </style>
    """
    html_code = """
    <ol class="breadcrumb">
        <li><span class="{mode1}">🏠 HOME</span></li>
        <li><span class="{mode2}">item2</span></li>
        <li><span class="{mode3}">item3</span></li>
    </ol>
    """
    st.html(css_code)
    st.html(html_code.format(mode1="active", mode2="inactive", mode3="inactive"))

show_breadcrumb()