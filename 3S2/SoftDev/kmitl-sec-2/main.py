import streamlit as st
pg = st.navigation([
st.Page("page1.py", title="Page #1", icon=":material/counter_1:"),
st.Page("page2.py", title="Page #2", icon=":material/counter_2:"),
])
pg.run()