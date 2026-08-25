import os
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QFileDialog,
    QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QGroupBox, QMessageBox, QFrame, QDialog, QListWidget,
    QListWidgetItem, QRadioButton, QButtonGroup, QCheckBox
)
from PySide6.QtCore import Qt, Slot, QThread, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon

from gui.styles import DARK_THEME_QSS
from utils.csv_handler import CSVHandler
from utils.updater import AutoUpdater, UpdateDownloadThread
from storage.state_manager import StateManager
from engine.rank_checker import RankCheckerThread, COUNTRY_DOMAINS

def get_asset_icon(icon_name: str) -> QIcon:
    """Helper to fetch crisp HD vector icon from assets folder."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", icon_name)
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()

class UpdateCheckThread(QThread):
    update_checked = Signal(bool, str, str, str, str)

    def run(self):
        has_update, latest_ver, notes, download_url, sha256 = AutoUpdater.check_for_update()
        self.update_checked.emit(has_update, latest_ver, notes, download_url, sha256)


class UpdateDialog(QDialog):
    """
    Dialog displaying Update Details, Live Download Progress Bar & Asynchronous Download Thread.
    Keeps UI 100% responsive without showing '(Not Responding)'.
    """
    def __init__(self, current_ver: str, latest_ver: str, notes: str, download_url: str, expected_sha256: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"App Update Available - v{latest_ver}")
        self.resize(500, 380)
        self.setStyleSheet(DARK_THEME_QSS)

        self.download_url = download_url
        self.expected_sha256 = expected_sha256
        self.dl_thread: Optional[UpdateDownloadThread] = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        lbl_header = QLabel(f"🚀 New Update Available: v{latest_ver}")
        lbl_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #89B4FA;")
        layout.addWidget(lbl_header)

        lbl_ver = QLabel(f"Current Version: v{current_ver}   ➜   Latest Version: v{latest_ver}")
        lbl_ver.setStyleSheet("color: #A6E3A1; font-weight: bold;")
        layout.addWidget(lbl_ver)

        # Release Notes
        lbl_notes_title = QLabel("Release Notes:")
        lbl_notes_title.setStyleSheet("font-weight: bold; color: #CDD6F4;")
        layout.addWidget(lbl_notes_title)

        txt_notes = QTextEdit()
        txt_notes.setReadOnly(True)
        txt_notes.setText(notes if notes else "Performance enhancements and stability updates.")
        txt_notes.setStyleSheet("background-color: #181825; border: 1px solid #313244; color: #CDD6F4;")
        layout.addWidget(txt_notes)

        # Live Download Progress Bar & Status Text
        self.lbl_progress_status = QLabel("")
        self.lbl_progress_status.setStyleSheet("color: #89B4FA; font-weight: bold;")
        self.lbl_progress_status.setVisible(False)
        layout.addWidget(self.lbl_progress_status)

        self.dl_progress_bar = QProgressBar()
        self.dl_progress_bar.setValue(0)
        self.dl_progress_bar.setVisible(False)
        layout.addWidget(self.dl_progress_bar)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_close = QPushButton("Later")
        self.btn_close.clicked.connect(self.reject)

        self.btn_install = QPushButton("Download & Install Update")
        self.btn_install.setIcon(get_asset_icon("icon_refresh.png"))
        self.btn_install.setIconSize(QSize(18, 18))
        self.btn_install.setObjectName("btnStart")
        self.btn_install.clicked.connect(self.on_install)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        btn_layout.addWidget(self.btn_install)
        layout.addLayout(btn_layout)

    def on_install(self):
        if not self.download_url:
            QMessageBox.warning(self, "Update Error", "Update could not be downloaded. Please check your internet connection and try again.")
            return

        self.btn_install.setEnabled(False)
        self.btn_close.setEnabled(False)
        self.lbl_progress_status.setVisible(True)
        self.dl_progress_bar.setVisible(True)
        self.lbl_progress_status.setText("Initializing update package download...")

        self.dl_thread = UpdateDownloadThread(self.download_url, self.expected_sha256)
        self.dl_thread.progress_updated.connect(self.on_download_progress)
        self.dl_thread.download_finished.connect(self.on_download_finished)
        self.dl_thread.start()

    @Slot(int, int, str, int)
    def on_download_progress(self, downloaded: int, total: int, speed_str: str, percent: int):
        self.dl_progress_bar.setValue(percent)
        dl_mb = downloaded / (1024 * 1024)
        tot_mb = total / (1024 * 1024)
        if total > 0:
            self.lbl_progress_status.setText(f"Downloading Update: {dl_mb:.1f} MB / {tot_mb:.1f} MB ({percent}%) @ {speed_str}")
        else:
            self.lbl_progress_status.setText(f"Downloading Update: {dl_mb:.1f} MB @ {speed_str}")

    @Slot(bool, str)
    def on_download_finished(self, success: bool, msg: str):
        if not success:
            QMessageBox.critical(self, "Update Status", msg)
            self.btn_install.setEnabled(True)
            self.btn_close.setEnabled(True)
            self.lbl_progress_status.setVisible(False)
            self.dl_progress_bar.setVisible(False)


class CountrySelectDialog(QDialog):
    """
    Searchable Country Selection Modal Dialog with a top search bar and instant filtering.
    """
    def __init__(self, current_country: str = "United States", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Target Country")
        self.resize(400, 500)
        self.setStyleSheet(DARK_THEME_QSS)
        self.selected_country = current_country

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(14, 14, 14, 14)

        # Top Search Bar
        lbl_info = QLabel("Search Target Country:")
        lbl_info.setStyleSheet("font-weight: bold; color: #89B4FA;")
        layout.addWidget(lbl_info)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Type country name to filter (e.g. Australia, Pakistan)...")
        self.txt_search.textChanged.connect(self.filter_countries)
        layout.addWidget(self.txt_search)

        # Country List
        self.list_countries = QListWidget()
        self.list_countries.setStyleSheet("""
            QListWidget {
                background-color: #1E1E2E;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 4px;
                color: #CDD6F4;
            }
            QListWidget::item:selected {
                background-color: #89B4FA;
                color: #11111B;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #313244;
            }
        """)
        self.populate_list()
        self.list_countries.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_countries)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Select Country")
        btn_ok.setObjectName("btnStart")
        btn_ok.clicked.connect(self.on_accept)
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.txt_search.setFocus()

    def populate_list(self):
        self.list_countries.clear()
        for country in sorted(COUNTRY_DOMAINS.keys()):
            item = QListWidgetItem(country)
            self.list_countries.addItem(item)
            if country == self.selected_country:
                self.list_countries.setCurrentItem(item)

    def filter_countries(self, query: str):
        q = query.strip().lower()
        for i in range(self.list_countries.count()):
            item = self.list_countries.item(i)
            item.setHidden(q not in item.text().lower())

    def on_item_double_clicked(self, item):
        self.selected_country = item.text()
        self.accept()

    def on_accept(self):
        current_item = self.list_countries.currentItem()
        if current_item:
            self.selected_country = current_item.text()
        self.accept()


class MetricCard(QFrame):
    def __init__(self, title: str, initial_value: str = "0", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("metricTitle")
        
        self.lbl_value = QLabel(initial_value)
        self.lbl_value.setObjectName("metricValue")
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)

    def set_value(self, value: str):
        self.lbl_value.setText(str(value))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Google Keyword Rank Checker v{AutoUpdater.get_current_version()}")
        self.resize(1180, 840)
        self.setStyleSheet(DARK_THEME_QSS)

        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.state_manager = StateManager(storage_dir="data")
        self.worker_thread: Optional[RankCheckerThread] = None
        self.update_thread: Optional[UpdateCheckThread] = None
        self.keywords_list: List[str] = []
        self.selected_country: str = "United States"

        self.latest_ver: str = AutoUpdater.get_current_version()
        self.release_notes: str = ""
        self.download_url: str = ""
        self.expected_sha256: str = ""
        self.has_update_available: bool = False

        self.init_ui()
        self.load_saved_session_state()
        self.check_for_updates_async()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # ---------------- 1. Configuration & Inputs Section ----------------
        input_box = QGroupBox("Configuration & Inputs")
        input_grid = QGridLayout(input_box)
        input_grid.setHorizontalSpacing(16)
        input_grid.setVerticalSpacing(10)

        # Target Domain (Row 0)
        input_grid.addWidget(QLabel("Target Domain:"), 0, 0)
        self.txt_domain = QLineEdit()
        self.txt_domain.setPlaceholderText("e.g. example.com")
        input_grid.addWidget(self.txt_domain, 0, 1)

        # Target Country (Row 0) with HD Vector Globe Icon
        input_grid.addWidget(QLabel("Target Country:"), 0, 2)
        self.btn_select_country = QPushButton(f"  {self.selected_country}  ▾")
        self.btn_select_country.setIcon(get_asset_icon("icon_globe.png"))
        self.btn_select_country.setIconSize(QSize(18, 18))
        self.btn_select_country.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding-left: 12px;
                font-weight: bold;
                background-color: #313244;
                border: 1px solid #45475A;
            }
            QPushButton:hover {
                border-color: #89B4FA;
                background-color: #3B3E52;
            }
        """)
        self.btn_select_country.clicked.connect(self.on_open_country_dialog)
        input_grid.addWidget(self.btn_select_country, 0, 3)

        # Keywords CSV (Row 1)
        input_grid.addWidget(QLabel("Keywords File:"), 1, 0)
        csv_layout = QHBoxLayout()
        self.txt_csv_path = QLineEdit()
        self.txt_csv_path.setPlaceholderText("Select CSV / TXT file containing keywords...")
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.on_browse_csv)
        csv_layout.addWidget(self.txt_csv_path)
        csv_layout.addWidget(self.btn_browse)
        input_grid.addLayout(csv_layout, 1, 1)

        # Max Google Pages (Row 1) - Styled Dropdown ComboBox (1 to 10 Pages)
        input_grid.addWidget(QLabel("Max Google Pages:"), 1, 2)
        self.cmb_pages = QComboBox()
        for p in range(1, 11):
            top_num = p * 10
            lbl_p = f"{p} Page (Top {top_num})" if p == 1 else f"{p} Pages (Top {top_num})"
            self.cmb_pages.addItem(lbl_p, p)
        self.cmb_pages.setCurrentIndex(4) # Default 5 Pages (Top 50)
        input_grid.addWidget(self.cmb_pages, 1, 3)

        # Proxy (Optional) (Row 2) - Spans across columns matching inputs
        input_grid.addWidget(QLabel("Proxy (Optional):"), 2, 0)
        self.txt_proxy = QLineEdit()
        self.txt_proxy.setPlaceholderText("Optional: ip:port or ip:port:user:pass")
        input_grid.addWidget(self.txt_proxy, 2, 1, 1, 3)

        # Scan Mode Radio Buttons (Row 3)
        input_grid.addWidget(QLabel("Scan Mode:"), 3, 0)
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(20)

        self.rad_single = QRadioButton("Single Match (Stop on first found)")
        self.rad_multiple = QRadioButton("Multiple Occurrences (Scan all pages)")
        self.rad_single.setChecked(True)

        self.btn_group_mode = QButtonGroup(self)
        self.btn_group_mode.addButton(self.rad_single, 1)
        self.btn_group_mode.addButton(self.rad_multiple, 2)

        mode_layout.addWidget(self.rad_single)
        mode_layout.addWidget(self.rad_multiple)
        mode_layout.addStretch()

        input_grid.addLayout(mode_layout, 3, 1, 1, 3)

        # Timezone Checkbox Option (Row 4)
        input_grid.addWidget(QLabel("Timezone Mode:"), 4, 0)
        self.chk_override_tz = QCheckBox("Override Browser Timezone (Recommended when using VPN)")
        self.chk_override_tz.setToolTip("Check this option when connected to a VPN so browser timezone matches target country IP.")
        input_grid.addWidget(self.chk_override_tz, 4, 1, 1, 3)

        main_layout.addWidget(input_box)

        # ---------------- 2. CAPTCHA Banner ----------------
        self.captcha_banner = QWidget()
        self.captcha_banner.setObjectName("captchaBanner")
        captcha_layout = QHBoxLayout(self.captcha_banner)
        captcha_layout.setContentsMargins(12, 8, 12, 8)
        
        self.lbl_captcha = QLabel("⚠️ CAPTCHA REQUIRED! Please click the checkbox in Chrome (App will auto-resume upon solving).")
        self.lbl_captcha.setObjectName("captchaText")
        captcha_layout.addWidget(self.lbl_captcha)
        
        self.btn_captcha_resume = QPushButton("Resume Manually")
        self.btn_captcha_resume.setObjectName("btnResume")
        self.btn_captcha_resume.clicked.connect(self.on_toggle_pause_resume)
        captcha_layout.addWidget(self.btn_captcha_resume)
        
        self.captcha_banner.setVisible(False)
        main_layout.addWidget(self.captcha_banner)

        # ---------------- 3. Controls & Progress ----------------
        controls_layout = QHBoxLayout()
        
        # Combined Start / Stop Button with HD Vector Icon
        self.btn_start_stop = QPushButton(" Start Checking")
        self.btn_start_stop.setIcon(get_asset_icon("icon_play.png"))
        self.btn_start_stop.setIconSize(QSize(18, 18))
        self.btn_start_stop.setObjectName("btnStart")
        self.btn_start_stop.clicked.connect(self.on_toggle_start_stop)
        
        # Combined Pause / Resume Button with HD Vector Icon
        self.btn_pause_resume = QPushButton(" Pause")
        self.btn_pause_resume.setIcon(get_asset_icon("icon_pause.png"))
        self.btn_pause_resume.setIconSize(QSize(18, 18))
        self.btn_pause_resume.setObjectName("btnPause")
        self.btn_pause_resume.setEnabled(False)
        self.btn_pause_resume.clicked.connect(self.on_toggle_pause_resume)

        # Clear Session Button with HD Vector Icon
        self.btn_clear_session = QPushButton(" Clear Session Data")
        self.btn_clear_session.setIcon(get_asset_icon("icon_trash.png"))
        self.btn_clear_session.setIconSize(QSize(18, 18))
        self.btn_clear_session.setObjectName("btnClearSession")
        self.btn_clear_session.setToolTip("Deletes saved progress JSON state & clears table")
        self.btn_clear_session.clicked.connect(self.on_clear_session)

        # Export CSV Button with HD Vector Icon
        self.btn_export = QPushButton(" Export CSV")
        self.btn_export.setIcon(get_asset_icon("icon_export.png"))
        self.btn_export.setIconSize(QSize(18, 18))
        self.btn_export.clicked.connect(self.on_export_csv)

        # Update App Button with HD Vector Icon & Red Dot Badge
        self.btn_update = QPushButton(f" Update App (v{AutoUpdater.get_current_version()})")
        self.btn_update.setIcon(get_asset_icon("icon_refresh.png"))
        self.btn_update.setIconSize(QSize(18, 18))
        self.btn_update.setToolTip("Check for new application updates")
        self.btn_update.setStyleSheet("""
            QPushButton {
                background-color: #313244;
                color: #CDD6F4;
                border: 1px solid #45475A;
                padding: 6px 14px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                border-color: #89B4FA;
                background-color: #3B3E52;
            }
        """)
        self.btn_update.clicked.connect(self.on_check_update_manual)

        controls_layout.addWidget(self.btn_start_stop)
        controls_layout.addWidget(self.btn_pause_resume)
        controls_layout.addWidget(self.btn_clear_session)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_export)
        controls_layout.addWidget(self.btn_update)

        main_layout.addLayout(controls_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("Progress: 0 / 0 (0%)")
        main_layout.addWidget(self.progress_bar)

        # ---------------- 4. Metric Cards Bar ----------------
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(10)
        
        self.card_status = MetricCard("Status", "Idle")
        self.card_current_kw = MetricCard("Current Keyword", "-")
        self.card_completed = MetricCard("Completed / Total", "0 / 0")
        self.card_found = MetricCard("Found Count", "0")
        self.card_not_found = MetricCard("Not Found", "0")
        self.card_captcha = MetricCard("CAPTCHA Status", "OK")

        metrics_layout.addWidget(self.card_status)
        metrics_layout.addWidget(self.card_current_kw)
        metrics_layout.addWidget(self.card_completed)
        metrics_layout.addWidget(self.card_found)
        metrics_layout.addWidget(self.card_not_found)
        metrics_layout.addWidget(self.card_captcha)

        main_layout.addLayout(metrics_layout)

        # ---------------- 5. Results Table & Log Console ----------------
        table_group = QGroupBox("Live Ranking Results")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Keyword", "Domain", "Rank", "Google Page", "Ranking URL", "Checked At", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        
        table_layout.addWidget(self.table)
        main_layout.addWidget(table_group, stretch=2)

        # Activity Log Console
        log_group = QGroupBox("Activity Console")
        log_layout = QVBoxLayout(log_group)
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(110)
        log_layout.addWidget(self.log_console)
        main_layout.addWidget(log_group, stretch=1)

        # ---------------- 6. Footer Credit Bar ----------------
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 2, 0, 0)
        
        lbl_credit = QLabel("⚡ This tool is made by Mohammad A. Bakhtawer")
        lbl_credit.setObjectName("lblCredit")
        lbl_credit.setAlignment(Qt.AlignCenter)
        
        footer_layout.addWidget(lbl_credit)
        main_layout.addLayout(footer_layout)

    def check_for_updates_async(self):
        self.update_thread = UpdateCheckThread()
        self.update_thread.update_checked.connect(self.on_update_check_result)
        self.update_thread.start()

    @Slot(bool, str, str, str, str)
    def on_update_check_result(self, has_update: bool, latest_ver: str, notes: str, download_url: str, expected_sha256: str):
        self.has_update_available = has_update
        self.latest_ver = latest_ver
        self.release_notes = notes
        self.download_url = download_url
        self.expected_sha256 = expected_sha256

        if has_update:
            self.btn_update.setText(f" Update App 🔴 (v{latest_ver})")
            self.btn_update.setIcon(get_asset_icon("icon_refresh.png"))
            self.btn_update.setIconSize(QSize(18, 18))
            self.btn_update.setStyleSheet("""
                QPushButton {
                    background-color: #F38BA8;
                    color: #11111B;
                    border: 1px solid #F38BA8;
                    padding: 6px 14px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #E78284;
                }
            """)
            self.btn_update.setToolTip(f"New Update v{latest_ver} available! Click to download & install.")
            self.log_msg(f"[UPDATE] 🚀 New update v{latest_ver} is available! Click 'Update App 🔴' to install.")

    @Slot()
    def on_check_update_manual(self):
        if self.has_update_available:
            dlg = UpdateDialog(
                current_ver=AutoUpdater.get_current_version(),
                latest_ver=self.latest_ver,
                notes=self.release_notes,
                download_url=self.download_url,
                expected_sha256=self.expected_sha256,
                parent=self
            )
            dlg.exec()
        else:
            QMessageBox.information(
                self,
                "App Version",
                f"You are running the latest version of Google Rank Checker (v{AutoUpdater.get_current_version()})."
            )

    def load_saved_session_state(self):
        st = self.state_manager.state
        if st.get("target_domain"):
            self.txt_domain.setText(st["target_domain"])
        if st.get("csv_path") and os.path.exists(st["csv_path"]):
            self.txt_csv_path.setText(st["csv_path"])
        if st.get("target_country"):
            self.selected_country = st["target_country"]
            self.btn_select_country.setText(f"  {self.selected_country}  ▾")
            self.btn_select_country.setIcon(get_asset_icon("icon_globe.png"))
        if st.get("proxy"):
            self.txt_proxy.setText(st["proxy"])
        if st.get("max_pages"):
            idx = self.cmb_pages.findData(st["max_pages"])
            if idx >= 0:
                self.cmb_pages.setCurrentIndex(idx)
        if st.get("scan_mode") == "multiple":
            self.rad_multiple.setChecked(True)
        else:
            self.rad_single.setChecked(True)

        if st.get("override_timezone"):
            self.chk_override_tz.setChecked(True)
        else:
            self.chk_override_tz.setChecked(False)

        # Populate saved results into table
        saved_results = self.state_manager.get_results()
        if saved_results:
            self.log_msg(f"[SESSION] Loaded {len(saved_results)} saved results from previous session.")
            for res in saved_results:
                self.add_or_update_table_row(res)
            self.update_metrics_from_table()

    def log_msg(self, text: str):
        self.log_console.append(text)
        self.log_console.verticalScrollBar().setValue(self.log_console.verticalScrollBar().maximum())

    @Slot()
    def on_open_country_dialog(self):
        dlg = CountrySelectDialog(current_country=self.selected_country, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.selected_country = dlg.selected_country
            self.btn_select_country.setText(f"  {self.selected_country}  ▾")
            self.btn_select_country.setIcon(get_asset_icon("icon_globe.png"))
            self.log_msg(f"[CONFIG] Target country updated to: {self.selected_country}")

    @Slot()
    def on_browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Keywords File", "", "CSV / Text Files (*.csv *.txt);;All Files (*)"
        )
        if file_path:
            self.txt_csv_path.setText(file_path)
            try:
                kws = CSVHandler.load_keywords(file_path)
                self.keywords_list = kws
                self.log_msg(f"[CSV] Loaded {len(kws)} UNIQUE keywords (duplicates automatically removed) from '{os.path.basename(file_path)}'")
            except Exception as e:
                QMessageBox.critical(self, "CSV Error", f"Failed to parse CSV file: {e}")

    @Slot()
    def on_toggle_start_stop(self):
        # If thread is currently running, stop it
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.captcha_banner.setVisible(False)
            self.update_btn_start_stop(is_running=False)
            self.update_btn_pause_resume(is_running=False, is_paused=False)
            return

        # Otherwise, start checking
        domain = self.txt_domain.text().strip()
        csv_path = self.txt_csv_path.text().strip()
        country = self.selected_country
        proxy = self.txt_proxy.text().strip()
        max_pages = self.cmb_pages.currentData()
        scan_mode = "multiple" if self.rad_multiple.isChecked() else "single"
        override_timezone = self.chk_override_tz.isChecked()

        if not domain:
            QMessageBox.warning(self, "Input Error", "Please enter your Target Domain Name.")
            return

        if not csv_path or not os.path.exists(csv_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid Keywords CSV file.")
            return

        try:
            self.keywords_list = CSVHandler.load_keywords(csv_path)
        except Exception as e:
            QMessageBox.critical(self, "CSV Error", f"Error loading keywords file: {e}")
            return

        if not self.keywords_list:
            QMessageBox.warning(self, "CSV Error", "The selected file contains no keywords.")
            return

        # Initialize session state
        self.state_manager.init_session(domain, country, csv_path, max_pages, proxy, scan_mode, override_timezone)

        # Update button states
        self.update_btn_start_stop(is_running=True)
        self.update_btn_pause_resume(is_running=True, is_paused=False)
        self.captcha_banner.setVisible(False)
        self.card_captcha.set_value("OK")

        # Spawn worker thread
        self.worker_thread = RankCheckerThread(
            domain=domain,
            keywords=self.keywords_list,
            country=country,
            max_pages=max_pages,
            state_manager=self.state_manager,
            proxy_string=proxy,
            scan_mode=scan_mode,
            override_timezone=override_timezone,
            headless=False
        )

        self.worker_thread.status_changed.connect(self.on_status_changed)
        self.worker_thread.keyword_started.connect(self.on_keyword_started)
        self.worker_thread.keyword_completed.connect(self.on_keyword_completed)
        self.worker_thread.progress_updated.connect(self.on_progress_updated)
        self.worker_thread.captcha_detected.connect(self.on_captcha_detected)
        self.worker_thread.captcha_cleared.connect(self.on_captcha_auto_cleared)
        self.worker_thread.log_message.connect(self.log_msg)
        self.worker_thread.finished_processing.connect(self.on_finished)

        self.worker_thread.start()

    @Slot()
    def on_toggle_pause_resume(self):
        if not self.worker_thread:
            return

        if self.worker_thread.is_paused or self.worker_thread.in_captcha_state:
            # Resume
            self.captcha_banner.setVisible(False)
            self.card_captcha.set_value("OK")
            self.worker_thread.resume()
            self.update_btn_pause_resume(is_running=True, is_paused=False)
        else:
            # Pause
            self.worker_thread.pause()
            self.update_btn_pause_resume(is_running=True, is_paused=True)

    def update_btn_start_stop(self, is_running: bool):
        if is_running:
            self.btn_start_stop.setText(" Stop Checking")
            self.btn_start_stop.setIcon(get_asset_icon("icon_stop.png"))
            self.btn_start_stop.setObjectName("btnStop")
        else:
            self.btn_start_stop.setText(" Start Checking")
            self.btn_start_stop.setIcon(get_asset_icon("icon_play.png"))
            self.btn_start_stop.setObjectName("btnStart")
        self.btn_start_stop.setIconSize(QSize(18, 18))
        self.btn_start_stop.setStyle(self.btn_start_stop.style())

    def update_btn_pause_resume(self, is_running: bool, is_paused: bool):
        self.btn_pause_resume.setEnabled(is_running)
        if not is_running:
            self.btn_pause_resume.setText(" Pause")
            self.btn_pause_resume.setIcon(get_asset_icon("icon_pause.png"))
            self.btn_pause_resume.setObjectName("btnPause")
        elif is_paused:
            self.btn_pause_resume.setText(" Resume")
            self.btn_pause_resume.setIcon(get_asset_icon("icon_play.png"))
            self.btn_pause_resume.setObjectName("btnResume")
        else:
            self.btn_pause_resume.setText(" Pause")
            self.btn_pause_resume.setIcon(get_asset_icon("icon_pause.png"))
            self.btn_pause_resume.setObjectName("btnPause")
        self.btn_pause_resume.setIconSize(QSize(18, 18))
        self.btn_pause_resume.setStyle(self.btn_pause_resume.style())

    @Slot()
    def on_clear_session(self):
        reply = QMessageBox.question(
            self,
            "Clear Session Data",
            "Are you sure you want to clear all saved session data and table results?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.stop()
            
            self.state_manager.reset_state()
            self.table.setRowCount(0)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("Progress: 0 / 0 (0%)")
            
            self.card_status.set_value("Idle")
            self.card_current_kw.set_value("-")
            self.card_completed.set_value("0 / 0")
            self.card_found.set_value("0")
            self.card_not_found.set_value("0")
            self.card_captcha.set_value("OK")
            
            self.update_btn_start_stop(is_running=False)
            self.update_btn_pause_resume(is_running=False, is_paused=False)
            
            self.log_console.clear()
            self.log_msg("[INFO] Session state and table cleared. Ready for a new run.")
            QMessageBox.information(self, "Session Cleared", "Saved progress and session data cleared successfully.")

    @Slot(str)
    def on_status_changed(self, status: str):
        self.card_status.set_value(status)
        if status == "CAPTCHA REQUIRED":
            self.card_captcha.set_value("⚠️ CAPTCHA")
            self.update_btn_pause_resume(is_running=True, is_paused=True)

    @Slot(str, int, int)
    def on_keyword_started(self, keyword: str, current_idx: int, total: int):
        self.card_current_kw.set_value(keyword)

    @Slot(dict)
    def on_keyword_completed(self, result: Dict[str, Any]):
        self.add_or_update_table_row(result)
        self.update_metrics_from_table()
        
        # Auto-export updated results
        csv_path = self.txt_csv_path.text().strip()
        scan_mode = "multiple" if self.rad_multiple.isChecked() else "single"
        if csv_path:
            out_file = os.path.join(os.path.dirname(os.path.abspath(csv_path)), "rank_results_autosave.csv")
            CSVHandler.export_results(self.state_manager.get_results(), out_file, scan_mode=scan_mode)

    @Slot(int, int)
    def on_progress_updated(self, completed: int, total: int):
        pct = int((completed / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"Progress: {completed} / {total} ({pct}%)")
        self.card_completed.set_value(f"{completed} / {total}")

    @Slot(str)
    def on_captcha_detected(self, msg: str):
        self.captcha_banner.setVisible(True)
        self.card_captcha.set_value("⚠️ REQUIRED")
        self.update_btn_pause_resume(is_running=True, is_paused=True)

    @Slot()
    def on_captcha_auto_cleared(self):
        self.captcha_banner.setVisible(False)
        self.card_captcha.set_value("OK")
        self.update_btn_pause_resume(is_running=True, is_paused=False)

    @Slot()
    def on_finished(self):
        self.update_btn_start_stop(is_running=False)
        self.update_btn_pause_resume(is_running=False, is_paused=False)
        self.captcha_banner.setVisible(False)
        self.card_current_kw.set_value("-")
        
        csv_path = self.txt_csv_path.text().strip()
        if csv_path:
            out_file = os.path.join(os.path.dirname(os.path.abspath(csv_path)), "rank_results_autosave.csv")
            self.log_msg(f"\n[EXPORT] All rank results saved to: '{out_file}'")

    def add_or_update_table_row(self, res: Dict[str, Any]):
        kw = res.get("keyword", "")
        url = res.get("ranking_url", "")
        
        existing_row = -1
        # In multiple mode, check if exact kw + url already exists in table
        for row in range(self.table.rowCount()):
            kw_item = self.table.item(row, 0)
            url_item = self.table.item(row, 4)
            if kw_item and url_item:
                if kw_item.text() == kw and url_item.text() == url:
                    existing_row = row
                    break

        row = existing_row if existing_row != -1 else self.table.rowCount()
        if existing_row == -1:
            self.table.insertRow(row)

        status = res.get("status", "")
        
        item_kw = QTableWidgetItem(kw)
        item_domain = QTableWidgetItem(res.get("domain", ""))
        item_rank = QTableWidgetItem(str(res.get("rank", "N/A")))
        item_page = QTableWidgetItem(str(res.get("google_page", "N/A")))
        item_url = QTableWidgetItem(url)
        item_date = QTableWidgetItem(res.get("checked_at", ""))
        item_status = QTableWidgetItem(status)

        # Color coding status
        if status == "Found":
            item_status.setForeground(QColor("#A6E3A1"))
            item_rank.setForeground(QColor("#A6E3A1"))
        elif status == "Not Found":
            item_status.setForeground(QColor("#FAB387"))
        elif status in ["CAPTCHA", "Error"]:
            item_status.setForeground(QColor("#F38BA8"))

        self.table.setItem(row, 0, item_kw)
        self.table.setItem(row, 1, item_domain)
        self.table.setItem(row, 2, item_rank)
        self.table.setItem(row, 3, item_page)
        self.table.setItem(row, 4, item_url)
        self.table.setItem(row, 5, item_date)
        self.table.setItem(row, 6, item_status)

        self.table.scrollToItem(item_kw)

    def update_metrics_from_table(self):
        """
        Calculates Found and Not Found counts directly from StateManager completed keywords
        so that Found + Not Found matches Total Completed Unique Keywords 100% consistently.
        """
        completed_map = self.state_manager.get_completed_keywords()
        found_count = 0
        not_found_count = 0

        for kw, res_entry in completed_map.items():
            res_list = res_entry if isinstance(res_entry, list) else [res_entry]
            has_found = any(r.get("status") == "Found" for r in res_list)
            if has_found:
                found_count += 1
            else:
                has_not_found = any(r.get("status") == "Not Found" for r in res_list)
                if has_not_found:
                    not_found_count += 1

        self.card_found.set_value(str(found_count))
        self.card_not_found.set_value(str(not_found_count))

    @Slot()
    def on_export_csv(self):
        results = self.state_manager.get_results()
        if not results:
            QMessageBox.information(self, "Export", "No results available to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Results CSV", "google_rank_results.csv", "CSV Files (*.csv);;All Files (*)"
        )
        scan_mode = "multiple" if self.rad_multiple.isChecked() else "single"
        if file_path:
            try:
                CSVHandler.export_results(results, file_path, scan_mode=scan_mode)
                QMessageBox.information(self, "Export Success", f"Successfully exported {len(results)} rank results to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {e}")
