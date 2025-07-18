import pandas as pd
def generate_matches(df):
    matches = []
    for _, learner in df.iterrows():
        for _, teacher in df.iterrows():
            if (
                learner["WantsToLearn"] == teacher["CanTeach"]
                and learner["Name"] != teacher["Name"]
            ):
                matches.append({
                    "User1": learner["Name"],
                    "User2": teacher["Name"],
                    "SharedSkill": learner["WantsToLearn"]
                })
    return pd.DataFrame(matches)

# Example: Reading a CSV file
data = pd.read_csv('file.csv')
print(data.head())



