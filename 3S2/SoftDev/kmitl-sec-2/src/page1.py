# page1.py
import streamlit as st
import pandas as pd
st.title("My Data")
d = {'col1': [1, 2, 3, 4, 7], 'col2': [4, 5, 6, 9, 5], 'col3': [7, 8, 12, 1, 11]}
df = pd.DataFrame(data=d)
st.dataframe(df)
st.bar_chart(df, x='col1', y="col2")