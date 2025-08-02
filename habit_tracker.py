import pandas as pd
import os
import random
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer, util

# --- Setup ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
STUDY_LOG_FILE = os.path.join(DATA_DIR, "study_log.csv")
TARGET_FILE = os.path.join(DATA_DIR, "targets.csv")
model = SentenceTransformer("all-MiniLM-L6-v2")

# --- Load Registered Users ---
def load_users(user_file=USER_FILE):
    expected_cols = [
        "Name", "Email", "Gender", "AgeRange", "SkillLevel", "Role", "Timestamp",
        "CanTeach", "WantsToLearn", "StudyDays"
    ]
    
    if os.path.exists(user_file):
        try:
            df = pd.read_csv(user_file)
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = None
            df = df[expected_cols].drop_duplicates(subset="Email")
            return df
        except Exception as e:
            print("Error loading users:", e)
            return pd.DataFrame(columns=expected_cols)
    return pd.DataFrame(columns=expected_cols)

# --- Generate AI-Informed Study Targets ---
def get_study_targets(users_df, save_path=TARGET_FILE):
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

        total_target = base + boost + sim_score
        targets.append({"Name": row["Name"], "TargetMinutes": round(total_target, 2)})

    df = pd.DataFrame(targets)
    df.to_csv(save_path, index=False)
    return df

# --- Log Study Sessions ---
def log_study_activity(name, minutes, log_path=STUDY_LOG_FILE):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = pd.DataFrame([[name, minutes, timestamp]], columns=["Name", "Minutes", "Timestamp"])

    if os.path.exists(log_path):
        existing = pd.read_csv(log_path)
        df = pd.concat([existing, entry], ignore_index=True)
    else:
        df = entry

    df.to_csv(log_path, index=False)
    return df

# --- Simulate Study Check-ins (Testing Only) ---
def simulate_checkins(target_minutes, users_df):
    checkins = []

    for _, user in users_df.iterrows():
        name = user["Name"]
        # Simulate a check-in between 0 and the target_minutes
        minutes = random.randint(0, int(target_minutes))
        checkins.append({"Name": name, "CheckInMinutes": minutes})

    return pd.DataFrame(checkins)

# --- Weekly Study Summary for a User ---
def get_weekly_summary(name, log_path=STUDY_LOG_FILE):
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

# --- Identify Users Who Didn't Meet Their Weekly Target ---
def get_defaulters(target_path=TARGET_FILE, log_path=STUDY_LOG_FILE):
    if not os.path.exists(target_path) or not os.path.exists(log_path):
        return pd.DataFrame()

    targets = pd.read_csv(target_path)
    logs = pd.read_csv(log_path)

    if "Timestamp" not in logs.columns:
        return pd.DataFrame()

    logs["Timestamp"] = pd.to_datetime(logs["Timestamp"])
    recent_logs = logs[logs["Timestamp"] >= (datetime.now() - timedelta(days=7))]

    user_totals = recent_logs.groupby("Name")["Minutes"].sum().reset_index()
    merged = pd.merge(targets, user_totals, how="left", on="Name")
    merged["Minutes"] = merged["Minutes"].fillna(0)
    merged["MetTarget"] = merged["Minutes"] >= merged["TargetMinutes"]

    return merged[~merged["MetTarget"]]
