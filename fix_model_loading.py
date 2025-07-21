import os
import subprocess
import shutil
import sys

def run_pip_command(command):
    print(f"\n>>> Running: {command}")
    subprocess.check_call([sys.executable, "-m", "pip"] + command.split())

def uninstall_conflicting_packages():
    print("🔧 Uninstalling incompatible packages...")
    packages = ["torch", "torchvision", "torchaudio", "sentence-transformers", "transformers"]
    for package in packages:
        try:
            run_pip_command(f"uninstall -y {package}")
        except Exception as e:
            print(f"⚠️ Could not uninstall {package}: {e}")

def install_compatible_packages():
    print("📦 Installing compatible versions...")
    run_pip_command("install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2")
    run_pip_command("install sentence-transformers --upgrade")
    run_pip_command("install transformers --upgrade")

def delete_model_cache():
    print("🧹 Clearing model cache...")
    home = os.path.expanduser("~")
    cache_path = os.path.join(home, ".cache", "huggingface", "hub", "models--sentence-transformers--all-MiniLM-L6-v2")
    
    if os.path.exists(cache_path):
        try:
            shutil.rmtree(cache_path)
            print("✅ Deleted model cache successfully.")
        except Exception as e:
            print(f"❌ Failed to delete model cache: {e}")
    else:
        print("ℹ️ Model cache folder not found — skipping.")

def main():
    print("=== 🚀 Starting Fix Script for Meta Tensor Error ===")
    uninstall_conflicting_packages()
    install_compatible_packages()
    delete_model_cache()
    print("✅ All done! You can now rerun your Streamlit app.")
    print("👉 Run: streamlit run app.py")

if __name__ == "__main__":
    main()
