import json
import os
import sys
import urllib.request
import subprocess
import hashlib
import zipfile
from typing import Tuple, Optional, Dict, Any

APP_VERSION = "1.4"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/ma-bakhtawer/google_rank_checker/main/version.json"

class AutoUpdater:
    @staticmethod
    def get_current_version() -> str:
        return APP_VERSION

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        """
        Computes SHA-256 hash digest of a given file.
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest().lower()

    @staticmethod
    def check_for_update(remote_url: str = VERSION_CHECK_URL) -> Tuple[bool, str, str, str, str]:
        """
        Checks for application updates from remote URL.
        Returns: (has_update, latest_version, release_notes, download_url, expected_sha256)
        """
        try:
            req = urllib.request.Request(
                remote_url,
                headers={'User-Agent': 'GoogleRankChecker-AutoUpdater/1.4'}
            )
            with urllib.request.urlopen(req, timeout=6) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    latest_version = data.get("version", APP_VERSION)
                    notes = data.get("release_notes", "Performance improvements & bug fixes.")
                    download_url = data.get("download_url", "")
                    expected_sha256 = data.get("sha256", "").strip().lower()
                    
                    has_update = AutoUpdater._is_newer_version(APP_VERSION, latest_version)
                    return has_update, latest_version, notes, download_url, expected_sha256
        except Exception:
            pass
        
        return False, APP_VERSION, "", "", ""

    @staticmethod
    def _is_newer_version(current: str, latest: str) -> bool:
        try:
            c_parts = [int(x) for x in current.split('.')]
            l_parts = [int(x) for x in latest.split('.')]
            return l_parts > c_parts
        except Exception:
            return False

    @staticmethod
    def apply_update_and_restart(download_url: str, expected_sha256: str = "") -> Tuple[bool, str]:
        """
        Downloads update package, verifies SHA-256 hash & ZIP integrity,
        generates updater script, and restarts app cleanly.
        Returns: (success: bool, user_message: str)
        """
        update_dir = os.path.abspath(os.path.join("data", "updates"))
        os.makedirs(update_dir, exist_ok=True)
        zip_path = os.path.join(update_dir, "update.zip")

        # 1. Download Update ZIP
        try:
            req = urllib.request.Request(
                download_url,
                headers={'User-Agent': 'GoogleRankChecker-AutoUpdater/1.4'}
            )
            with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, 'wb') as out_file:
                out_file.write(response.read())
        except Exception as e:
            return False, "Update could not be downloaded. Please check your internet connection and try again."

        # 2. Verify ZIP Integrity
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 100:
            return False, "Update could not be downloaded. Please check your internet connection and try again."

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    return False, "Update failed. Your current version has not been changed."
        except Exception:
            return False, "Update failed. Your current version has not been changed."

        # 3. SHA-256 Checksum Verification
        if expected_sha256:
            actual_sha256 = AutoUpdater.compute_sha256(zip_path)
            if actual_sha256 != expected_sha256.lower():
                return False, "Update package verification failed (SHA-256 mismatch). Please try downloading again."

        # 4. Create Batch Script for Safe File Overwrite & Restart
        try:
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            bat_path = os.path.join(update_dir, "run_update.bat")
            exe_path = os.path.join(app_dir, "GoogleRankChecker.exe")
            
            bat_script = f"""@echo off
timeout /t 2 /nobreak > nul
powershell -Command "Expand-Archive -Path '{zip_path}' -DestinationPath '{app_dir}' -Force"
if exist "{exe_path}" (
    start "" "{exe_path}"
)
del "{zip_path}"
del "%~f0"
"""
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_script)
                
            subprocess.Popen(["cmd.exe", "/c", bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
            return True, "Update initiated successfully."
        except Exception:
            return False, "Update failed. Your current version has not been changed."
