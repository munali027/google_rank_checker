import subprocess
import sys
import os

def build():
    print("=" * 60)
    print("Building Google Rank Checker Standalone Executable (.exe)")
    print("=" * 60)

    # Ensure icon exists
    if not os.path.exists("assets/icon.ico"):
        import create_icon
        create_icon.create_app_icon()

    # PyInstaller command with custom icon and assets
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "GoogleRankChecker",
        "--icon", "assets/icon.ico",
        "--add-data", "gui;gui",
        "--add-data", "engine;engine",
        "--add-data", "storage;storage",
        "--add-data", "utils;utils",
        "--add-data", "assets;assets",
        "app.py"
    ]

    print(f"Running command: {' '.join(cmd)}")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        print("\n" + "=" * 60)
        print("SUCCESS! Executable built in 'dist/GoogleRankChecker/GoogleRankChecker.exe'")
        print("=" * 60)
    else:
        print("\nBuild failed with return code:", res.returncode)

if __name__ == "__main__":
    build()
