from pyngrok import ngrok
import os

# Connect to localhost:8501
public_url = ngrok.connect(8501)
print(f"🌐 SkillSpark is live at: {public_url}")

# Run Streamlit app
import subprocess
subprocess.Popen(["streamlit", "run", "app.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
