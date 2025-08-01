# habit_tracker.py (Reviewed + Enhanced)

import pandas as pd
import os
import random
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util

# --- Setup ---
DATA_DIR = "data"
DEFAULT_USER_FILE = os.path.join(DATA_DIR, "users.csv")
DEFAULT_STUDY_LOG = os.path.join(DATA_DIR, "study_log.csv")
DEFAULT_TARGETS_FILE = os.path.join(DATA_DIR, "targets.csv")
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Load users ---
def load_users():
    expected_cols = ["Name", "Email", "Gender", "AgeRange", "SkillLevel", "Role", "Timestamp", 
                     "CanTeach", "WantsToLearn", "StudyDays"]
    
    if os.path.exists(USER_FILE):
        try:
            df = pd.read_csv(USER_FILE)

            # Add any missing columns
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None

            df = df[expected_cols]  # reorder just in case
            df = df.drop_duplicates(subset="Email")
            return df
        except Exception as e:
            print("Error loading CSV:", e)
            return pd.DataFrame(columns=expected_cols)
    else:
        return pd.DataFrame(columns=expected_cols)


# --- AI-Inferred Study Target Suggestions ---
def get_study_targets(users_df, save_path=DEFAULT_TARGETS_FILE):
    """
    Infer weekly study targets based on learner-teacher similarity.
    """
    targets = []
    for _, row in users_df.iterrows():
        base = 30
        boost = 10 if str(row.get("SkillLevel", "")).lower() == "beginner" else 5
        wants = str(row.get("WantsToLearn", ""))
        teach = str(row.get("CanTeach", ""))

        try:
            sim_score = util.cos_sim(
                model.encode(wants, convert_to_tensor=True),
                model.encode(teach, convert_to_tensor=True)
            ).item() * 10
        except:
            sim_score = 0

        target = base + boost + sim_score
        targets.append({"Name": row["Name"], "TargetMinutes": round(target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(save_path, index=False)
    return df

# --- Log study session ---
def log_study_activity(name, minutes, log_path=DEFAULT_STUDY_LOG):
    """
    Log a study session with name, minutes, and timestamp.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[name, minutes, timestamp]], columns=["Name", "Minutes", "Timestamp"])
    if os.path.exists(log_path):
        existing = pd.read_csv(log_path)
        df = pd.concat([existing, entry], ignore_index=True)
    else:
        df = entry
    df.to_csv(log_path, index=False)
    return df

# --- Simulate check-ins for testing ---
def simulate_checkins(users_df, days=7, log_path=DEFAULT_STUDY_LOG):
    """
    Generate fake study data for demo/testing purposes.
    """
    all_logs = []
    for _, user in users_df.iterrows():
        for d in range(days):
            date = datetime.now() - timedelta(days=d)
            log_time = date.replace(hour=random.randint(8, 20), minute=random.randint(0, 59))
            if random.random() < 0.6:  # 60% chance of studying that day
                minutes = random.randint(20, 60)
                all_logs.append([user["Name"], minutes, log_time.strftime("%Y-%m-%d %H:%M:%S")])
    df = pd.DataFrame(all_logs, columns=["Name", "Minutes", "Timestamp"])
    df.to_csv(log_path, index=False)
    return df

# --- Weekly total study minutes per user ---
def get_weekly_summary(name, log_path=DEFAULT_STUDY_LOG):
    """
    Return a summary of study frequency over the last week for a user.
    """
    if not os.path.exists(log_path):
        return {}

    df = pd.read_csv(log_path)
    if "Timestamp" not in df.columns:
        return {}

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Day"] = df["Timestamp"].dt.day_name()
    df_user = df[df["Name"].str.lower() == name.lower()]

    summary = df_user["Day"].value_counts().reindex([
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ], fill_value=0).to_dict()

    return summary

# --- Identify users who didn’t meet their target ---
def get_defaulters(target_path=DEFAULT_TARGETS_FILE, log_path=DEFAULT_STUDY_LOG):
    """
    Return users who haven't met their weekly study targets.
    """
    if not os.path.exists(target_path) or not os.path.exists(log_path):
        return pd.DataFrame()

    targets = pd.read_csv(target_path)
    summary = pd.read_csv(log_path)
    if "Timestamp" not in summary.columns:
        return pd.DataFrame()

    summary["Timestamp"] = pd.to_datetime(summary["Timestamp"])
    last_week = datetime.now() - timedelta(days=7)
    recent = summary[summary["Timestamp"] >= last_week]
    user_totals = recent.groupby("Name")["Minutes"].sum().reset_index()

    merged = pd.merge(targets, user_totals, how="left", on="Name")
    merged["Minutes"] = merged["Minutes"].fillna(0)
    merged["MetTarget"] = merged["Minutes"] >= merged["TargetMinutes"]
    return merged[~merged["MetTarget"]]
