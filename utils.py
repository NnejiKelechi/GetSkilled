
import pandas as pd
from constants import USER_FILE

def safe_load_users():
    try:
        users = pd.read_csv(USER_FILE)
        users.fillna("", inplace=True)
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return pd.DataFrame()
