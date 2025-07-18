import pandas as pd
import os
import random
from datetime import datetime

# --- Constants ---
DATA_DIR = "data"
USER_FILE = os.path.join(DATA_DIR, "users.csv")
HABIT_FILE = os.path.join(DATA_DIR, "habit_log.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# --- Load Users ---
def load_users(data_file=USER_FILE):
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
    return pd.DataFrame(columns=["Name", "Username", "Email", "CanTeach", "WantsToLearn", "StudyTargetPerWeek", "JoinDate", "SkillLevel"])

# --- Study Targets Conversion ---
def get_study_targets(df):
    df["WeeklyTarget"] = pd.to_numeric(df["StudyTargetPerWeek"], errors="coerce").fillna(0).astype(int)
    return df

# --- Simulate Check-ins ---
def simulate_checkins(df):
    df = get_study_targets(df)
    df["CheckIns"] = df["WeeklyTarget"].apply(lambda x: random.randint(0, x))
    df["LogDate"] = datetime.now().strftime("%Y-%m-%d")
    return df

# --- Log Study Activity ---
def log_study_activity(name, skill, checkins):
    try:
        log_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_log = pd.DataFrame([[name, skill, checkins, log_date]], columns=["Name", "Skill", "CheckIns", "Timestamp"])
        if os.path.exists(HABIT_FILE):
            existing = pd.read_csv(HABIT_FILE)
            df = pd.concat([existing, new_log], ignore_index=True)
        else:
            df = new_log
        df.to_csv(HABIT_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error logging activity: {e}")
        return False

# --- Match Engine: Find Matches ---
def find_matches(data_file=USER_FILE):
    if not os.path.exists(data_file):
        return []

    df = pd.read_csv(data_file)

    matches = []
    matched_learners = set()
    matched_teachers = set()
    level_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}

    if "SkillLevel" not in df.columns:
        df["SkillLevel"] = "Intermediate"

    for _, learner in df.sample(frac=1).iterrows():
        learner_name = learner["Name"]
        learner_skill = learner["WantsToLearn"]
        learner_level = level_order.get(learner["SkillLevel"], 1)

        if learner_name in matched_learners:
            continue

        potential_teachers = df[(df["CanTeach"] == learner_skill) &
                                (df["Name"] != learner_name) &
                                (~df["Name"].isin(matched_teachers))]

        for _, teacher in potential_teachers.iterrows():
            teacher_level = level_order.get(teacher["SkillLevel"], 3)
            if teacher_level > learner_level:
                teacher_name = teacher["Name"]
                matches.append({
                    "Learner": learner_name,
                    "Teacher": teacher_name,
                    "Skill": learner_skill,
                    "LearnerSkillLevel": learner["SkillLevel"],
                    "TeacherSkillLevel": teacher["SkillLevel"]
                })
                matched_learners.add(learner_name)
                matched_teachers.add(teacher_name)
                break

    return matches
