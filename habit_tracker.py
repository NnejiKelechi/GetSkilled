# habit_tracker.py (AI-powered version)

import pandas as pd
import os
import random
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util

# --- Setup ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
STUDY_LOG = os.path.join(DATA_DIR, "study_log.csv")
TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Load users ---
def load_users():
    if os.path.exists(USER_FILE):
        df = pd.read_csv(USER_FILE)
        df = df.drop_duplicates(subset="Email")
        return df
    else:
        return pd.DataFrame()

# --- AI-Inferred Study Target Suggestions ---
def get_study_targets(users_df):
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if row.get("SkillLevel", "").lower() == "beginner" else 5

        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        sim_score = util.cos_sim(
            model.encode(wants, convert_to_tensor=True),
            model.encode(teach, convert_to_tensor=True)
        ).item() * 10

        target = base + boost + sim_score
        targets.append({"Name": row.Name, "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(TARGETS_FILE, index=False)
    return df

# --- Log study session ---
def log_study_activity(name, minutes):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[name, minutes, timestamp]], columns=["Name", "Minutes", "Timestamp"])
    if os.path.exists(STUDY_LOG):
        existing = pd.read_csv(STUDY_LOG)
        df = pd.concat([existing, entry], ignore_index=True)
    else:
        df = entry
    df.to_csv(STUDY_LOG, index=False)
    return df

# --- Simulate check-ins for testing ---
def simulate_checkins(users_df, days=7):
    all_logs = []
    for _, user in users_df.iterrows():
        for d in range(days):
            date = datetime.now() - timedelta(days=d)
            log_time = date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            if random.random() < 0.6:
                minutes = random.randint(20, 60)
                all_logs.append([user["Name"], minutes, log_time.strftime("%Y-%m-%d %H:%M:%S")])
    df = pd.DataFrame(all_logs, columns=["Name", "Minutes", "Timestamp"])
    df.to_csv(STUDY_LOG, index=False)
    return df

# --- Weekly total study minutes per user ---
def get_weekly_summary(user_name):
    if os.path.exists(STUDY_LOG):
        df = pd.read_csv(STUDY_LOG)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])
        last_week = datetime.now() - timedelta(days=7)
        recent = df[(df["Timestamp"] >= last_week) & (df["Name"].str.lower() == user_name.lower())]
        if recent.empty:
            return {}

        daily = recent.groupby(recent["Timestamp"].dt.strftime("%A"))['Minutes'].sum().to_dict()
        return daily
    else:
        return {}

# --- Identify users who didn’t meet their target ---
def get_defaulters():
    if not os.path.exists(TARGETS_FILE) or not os.path.exists(STUDY_LOG):
        return pd.DataFrame()

    targets = pd.read_csv(TARGETS_FILE)
    summary = pd.read_csv(STUDY_LOG)
    summary["Timestamp"] = pd.to_datetime(summary["Timestamp"])
    last_week = datetime.now() - timedelta(days=7)
    recent = summary[summary["Timestamp"] >= last_week]
    user_totals = recent.groupby("Name")["Minutes"].sum().reset_index()

    merged = pd.merge(targets, user_totals, how="left", on="Name")
    merged["Minutes"] = merged["Minutes"].fillna(0)
    merged["MetTarget"] = merged["Minutes"] >= merged["TargetMinutes"]
    return merged[~merged["MetTarget"]]
