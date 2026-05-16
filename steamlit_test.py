import streamlit as st

st.title("My First App")

name = st.text_input("Enter your name")
st.write("Hello", name)