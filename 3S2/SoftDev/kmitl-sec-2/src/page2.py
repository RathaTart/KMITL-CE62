# page2.py
import streamlit as st
import pandas as pd
st.title("My Data")
uploaded_file = st.file_uploader("อัปโหลดไฟล์ CSV เพื่อเข้าสู่ระบบ"

, type=['csv'])

if uploaded_file:
    dataFrame = pd.read_csv(uploaded_file, header=0, sep=",")
    st.dataframe(dataFrame)