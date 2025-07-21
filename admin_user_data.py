# admin_user_data.py
import os
import streamlit as st
import pandas as pd
from habit_tracker import safe_load_users

USER_FILE = "data/users.csv"

def render_user_data_tab():
    st.markdown("### 👥 Manage User Data")
    if st.button("🩹 Clean & Format User Data"):
        users = safe_load_users()
        users.to_csv(USER_FILE, index=False)
        st.success("✅ Data cleaned and saved successfully.")

    if os.path.exists(USER_FILE):
        st.dataframe(pd.read_csv(USER_FILE))
