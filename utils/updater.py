import json
import os
import sys
import time
import urllib.request
import subprocess
import hashlib
import zipfile
from typing import Tuple, Optional, Dict, Any

from PySide6.QtCore import QThread, Signal

APP_VERSION = "1.7"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/ma-bakhtawer/google_rank_checker/main/version.json"

class UpdateDownloadThread(QThread):
    """
    Asynchronous Thread for Downloading Update ZIP with live progress & speed calculations.
    Keeps Qt GUI 100% responsive without showing '(Not Responding)'.
    """
    progress_updated = Signal(int, int, str, int)  # (downloaded_bytes, total_bytes, speed_str, percent)
    download_finished = Signal(bool, str)          # (success, message)

    def __init__(self, download_url: str, expected_sha256: str = ""):
        super().__init__()
        self.download_url = download_url
        self.expected_sha256 = expected_sha256.strip().lower()

    def run(self):
        update_dir = os.path.abspath(os.path.join("data", "updates"))
        os.makedirs(update_dir, exist_ok=True)
        zip_path = os.path.join(update_dir, "update.zip")

        # 1. Chunked HTTP Download with live progress calculation
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': 'GoogleRankChecker-AutoUpdater/1.4'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 65536
                start_time = time.time()
                
                with open(zip_path, 'wb') as out_file:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        
                        elapsed = time.time() - start_time
                        speed_mbps = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
                        pct = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        
                        self.progress_updated.emit(downloaded, total_size, f"{speed_mbps:.1f} MB/s", pct)

        except Exception:
            self.download_finished.emit(False, "Update could not be downloaded. Please check your internet connection and try again.")
            return

        # 2. Verify ZIP Integrity
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 100:
            self.download_finished.emit(False, "Update could not be downloaded. Please check your internet connection and try again.")
            return

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    self.download_finished.emit(False, "Update failed. Your current version has not been changed.")
                    return
        except Exception:
            self.download_finished.emit(False, "Update failed. Your current version has not been changed.")
            return

        # 3. SHA-256 Checksum Verification
        if self.expected_sha256:
            actual_sha256 = AutoUpdater.compute_sha256(zip_path)
            if actual_sha256 != self.expected_sha256:
                self.download_finished.emit(False, "Update package verification failed (SHA-256 mismatch). Please try downloading again.")
                return

        # 4. Create Batch Script & Launch Restart
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
            self.download_finished.emit(True, "Update applied successfully! Restarting application...")
            sys.exit(0)
        except Exception:
            self.download_finished.emit(False, "Update failed. Your current version has not been changed.")


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
