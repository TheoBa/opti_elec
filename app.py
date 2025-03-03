import streamlit as st

st.set_page_config(
    page_title='Homepage', 
    page_icon='😎', 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def welcome_page():
    st.title("Welcome to the Epsilon project homepage!")
    st.markdown("This is the homepage of the Epsilon project. Here you can find information about the project, the team, and the results.")
    st.markdown("⬅️To navigate through the project, use the sidebar on the left.")


if __name__=="__main__":
    welcome_page()