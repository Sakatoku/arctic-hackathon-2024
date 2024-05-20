import streamlit as st
import time

def long_long_process():
    for i in range(100):
        time.sleep(10)
        st.write(f"Processing... {i+1}%")

long_long_process()