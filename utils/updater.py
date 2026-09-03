import json
import os
import sys
import time
import shutil
import urllib.request
import subprocess
import hashlib
import zipfile
from typing import Tuple, Optional, Dict, Any

from PySide6.QtCore import QThread, Signal

APP_VERSION = "1.9"
VERSION_CHECK_URL = "https://raw.githubusercontent.com/ma-bakhtawer/google_rank_checker/main/version.json"

class UpdateDownloadThread(QThread):
    """
    Asynchronous Thread for Downloading, Verifying & Extracting Update Packages with live progress.
    Keeps Qt GUI 100% responsive and handles both flat and wrapped ZIP distributions.
    """
    download_progress = Signal(int, int, str, int)  # (downloaded_bytes, total_bytes, speed_str, percent)
    install_progress = Signal(int, int, str, int)   # (extracted_files, total_files, file_name, percent)
    status_message = Signal(str)
    update_ready = Signal(str, str)                 # (bat_path, target_exe_path)
    update_failed = Signal(str)                     # error_message

    def __init__(self, download_url: str, expected_sha256: str = ""):
        super().__init__()
        self.download_url = download_url
        self.expected_sha256 = expected_sha256.strip().lower()

    def run(self):
        update_dir = os.path.abspath(os.path.join("data", "updates"))
        staging_dir = os.path.join(update_dir, "staging")
        zip_path = os.path.join(update_dir, "update.zip")

        os.makedirs(update_dir, exist_ok=True)
        if os.path.exists(staging_dir):
            try:
                shutil.rmtree(staging_dir)
            except Exception:
                pass
        os.makedirs(staging_dir, exist_ok=True)

        # ---------------- Phase 1: Download Update Package ----------------
        self.status_message.emit("Connecting to update server...")
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={'User-Agent': f'GoogleRankChecker-AutoUpdater/{APP_VERSION}'}
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
                        
                        self.download_progress.emit(downloaded, total_size, f"{speed_mbps:.1f} MB/s", pct)

        except Exception as e:
            self.update_failed.emit(f"Update could not be downloaded ({e}). Please check your internet connection and try again.")
            return

        # ---------------- Phase 2: Verify ZIP Integrity & Checksum ----------------
        self.status_message.emit("Verifying package integrity...")
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 100:
            self.update_failed.emit("Update package is empty or invalid. Please try downloading again.")
            return

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                if zip_ref.testzip() is not None:
                    self.update_failed.emit("Update package is corrupted. Your current version has not been changed.")
                    return
        except Exception:
            self.update_failed.emit("Failed to open update archive. Your current version has not been changed.")
            return

        if self.expected_sha256:
            actual_sha256 = AutoUpdater.compute_sha256(zip_path)
            if actual_sha256 != self.expected_sha256:
                self.update_failed.emit("Update verification failed (SHA-256 mismatch). Your current version has not been changed.")
                return

        # ---------------- Phase 3: Extract with Live Progress Bar ----------------
        self.status_message.emit("Extracting update files...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.infolist()
                total_files = len(file_list)
                
                for idx, file_info in enumerate(file_list, start=1):
                    zip_ref.extract(file_info, staging_dir)
                    pct = int((idx / total_files) * 100)
                    fname = os.path.basename(file_info.filename)
                    if fname:
                        self.install_progress.emit(idx, total_files, fname, pct)

        except Exception as e:
            self.update_failed.emit(f"Extraction failed ({e}). Your current version has not been changed.")
            return

        # ---------------- Phase 4: Normalize Folder Structure ----------------
        # If the ZIP contained a wrapped root folder (e.g. GoogleRankChecker/GoogleRankChecker.exe), flatten it
        final_source_dir = staging_dir
        sub_items = [os.path.join(staging_dir, x) for x in os.listdir(staging_dir)]
        if len(sub_items) == 1 and os.path.isdir(sub_items[0]):
            nested_exe = os.path.join(sub_items[0], "GoogleRankChecker.exe")
            if os.path.exists(nested_exe):
                final_source_dir = sub_items[0]

        # Determine target application directory
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        target_exe = os.path.join(app_dir, "GoogleRankChecker.exe")

        # ---------------- Phase 5: Generate Robust Windows Updater Batch ----------------
        bat_path = os.path.join(update_dir, "apply_update.bat")
        bat_content = f"""@echo off
title Google Rank Checker - Updating to v{APP_VERSION}
echo Waiting for application to close...
taskkill /F /IM GoogleRankChecker.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

echo Copying update files to {app_dir}...
robocopy "{final_source_dir}" "{app_dir}" /E /IS /IT /NP /R:5 /W:1 >nul

echo Launching updated application...
start "" "{target_exe}"

timeout /t 1 /nobreak >nul
del "{zip_path}" >nul 2>&1
rmdir /S /Q "{staging_dir}" >nul 2>&1
(goto) 2>nul & del "%~f0"
"""
        try:
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(bat_content)
        except Exception as e:
            self.update_failed.emit(f"Failed to create update script ({e}).")
            return

        self.status_message.emit("Update ready! Restarting application...")
        self.update_ready.emit(bat_path, target_exe)


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
                headers={'User-Agent': f'GoogleRankChecker-AutoUpdater/{APP_VERSION}'}
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
