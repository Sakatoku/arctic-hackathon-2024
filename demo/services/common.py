# Common functions

# Streamlit: https://www.streamlit.io/
import streamlit as st

def show_title():
    st.image("./resources/imgs/logo.svg")

def show_breadcrumb(active_mode: int):
    # set mode
    mode1 = "active" if active_mode == 0 else "inactive"
    mode2 = "active" if active_mode == 1 else "inactive"
    mode3 = "active" if active_mode == 2 else "inactive"

    # embed css and html
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
        <li><span class="{mode2}">💬 SAKATALK</span></li>
        <li><span class="{mode3}">🛫 PLAN</span></li>
    </ol>
    """
    st.divider()
    st.html(css_code)
    st.html(html_code.format(mode1=mode1, mode2=mode2, mode3=mode3))
