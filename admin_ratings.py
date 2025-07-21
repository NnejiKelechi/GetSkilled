import streamlit as st
import pandas as pd
import os

RATINGS_FILE = "data/ratings.csv"

def show_ratings_tab():
    st.markdown("### 🌟 Submitted Ratings")
    
    if os.path.exists(RATINGS_FILE):
        ratings_df = pd.read_csv(RATINGS_FILE)
        st.dataframe(ratings_df)
    else:
        st.info("No ratings file found yet.")
