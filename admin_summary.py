import streamlit as st
import pandas as pd
import os

USER_FILE = "data/users.csv"
MATCH_FILE = "data/matches.csv"

def show_summary_tab():
    st.markdown("### 📋 User Match Summary")

    if not os.path.exists(USER_FILE):
        st.warning("User file not found.")
        return

    all_users = pd.read_csv(USER_FILE)
    all_users["Name"] = all_users["Name"].astype(str).str.strip().str.lower()

    if os.path.exists(MATCH_FILE):
        matches = pd.read_csv(MATCH_FILE)
        matches["Learner"] = matches["Learner"].astype(str).str.lower()
        matches["Teacher"] = matches["Teacher"].astype(str).str.lower()

        matched_names = set(matches["Learner"]) | set(matches["Teacher"])
        all_users["Match Status"] = all_users["Name"].apply(
            lambda n: "Paired" if n in matched_names else "Unpaired"
        )

        st.subheader("📊 All Users with Match Status")
        st.dataframe(all_users[[
            "Name", "Email", "Gender", "SkillLevel", "Role", 
            "CanTeach", "WantsToLearn", "Timestamp", "Match Status"
        ]])

        st.subheader("❌ Unpaired Users")
        unpaired_users = all_users[all_users["Match Status"] == "Unpaired"]
        st.dataframe(unpaired_users[[
            "Name", "Email", "Gender", "SkillLevel", "Role", 
            "CanTeach", "WantsToLearn", "Timestamp"
        ]])
    else:
        st.info("No match data available.")
