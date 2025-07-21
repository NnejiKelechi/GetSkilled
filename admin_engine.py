import streamlit as st
import pandas as pd
import os
from match_engine import find_matches

USER_FILE = "data/users.csv"
MATCH_FILE = "data/matches.csv"

def show_engine_tab():
    st.markdown("### ⚙️ Run AI Matching Engine")

    if not os.path.exists(USER_FILE):
        st.warning("User file not found.")
        return

    if st.button("🔄 Re-run AI Matching"):
        user_df = pd.read_csv(USER_FILE)

        # Ensure required columns exist
        if not {"Name", "Email", "CanTeach", "WantsToLearn", "Role"}.issubset(user_df.columns):
            st.error("❌ Required user fields missing. Please check your CSV.")
            return

        matches = find_matches(user_df, threshold=0.6, show_progress=True)
        pd.DataFrame(matches).to_csv(MATCH_FILE, index=False)

        st.success("✅ Matches re-generated and saved.")
        st.dataframe(pd.DataFrame(matches))
