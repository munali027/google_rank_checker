import json
import os
import sys
import urllib.request
import subprocess
from typing import Tuple, Optional, Dict, Any

APP_VERSION = "1.3"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/ma-bakhtawer/google_rank_checker/main/version.json"

class AutoUpdater:
    @staticmethod
    def get_current_version() -> str:
        return APP_VERSION

    @staticmethod
    def check_for_update(remote_url: str = VERSION_CHECK_URL) -> Tuple[bool, str, str, str]:
        """
        Checks for application updates from remote URL.
        Returns: (has_update, latest_version, release_notes, download_url)
        """
        try:
            req = urllib.request.Request(
                remote_url,
                headers={'User-Agent': 'GoogleRankChecker-AutoUpdater/1.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get("version", APP_VERSION)
                    notes = data.get("release_notes", "Performance improvements & bug fixes.")
                    download_url = data.get("download_url", "")
                    
                    has_update = AutoUpdater._is_newer_version(APP_VERSION, latest_version)
                    return has_update, latest_version, notes, download_url
        except Exception:
            pass
        
        return False, APP_VERSION, "", ""

    @staticmethod
    def _is_newer_version(current: str, latest: str) -> bool:
        try:
            c_parts = [int(x) for x in current.split('.')]
            l_parts = [int(x) for x in latest.split('.')]
            return l_parts > c_parts
        except Exception:
            return False

    @staticmethod
    def apply_update_and_restart(download_url: str) -> bool:
        """
        Downloads update package, generates updater batch script, and restarts app cleanly.
        """
        try:
            update_dir = os.path.abspath(os.path.join("data", "updates"))
            os.makedirs(update_dir, exist_ok=True)
            
            # Download file
            zip_path = os.path.join(update_dir, "update.zip")
            urllib.request.urlretrieve(download_url, zip_path)
            
            # Create updater batch script
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            bat_path = os.path.join(update_dir, "run_update.bat")
            exe_path = os.path.join(app_dir, "GoogleRankChecker.exe")
            
            bat_script = f"""@echo off
timeout /t 2 /nobreak > nul
powershell -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '{app_dir}' -Force"
start "" "{exe_path}"
del "{zip_path}"
del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_script)
                
            subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
            return True
        except Exception as e:
            print(f"Update failed: {e}")
            return False
