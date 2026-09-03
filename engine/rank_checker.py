import time
import random
import re
import sys
import io
import os
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime
from typing import List, Dict, Any, Optional

from PySide6.QtCore import QThread, Signal

from playwright.sync_api import sync_playwright, BrowserContext, Page
from engine.captcha_handler import CaptchaHandler
from storage.state_manager import StateManager

# Redirect stdout/stderr if None in PyInstaller --windowed mode
if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

# Fix Playwright browser path in PyInstaller frozen app mode
if getattr(sys, 'frozen', False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"

# Worldwide Google domain, language, locale and timezone mapping
COUNTRY_DOMAINS = {
    "United States": {"base": "https://www.google.com", "gl": "us", "hl": "en", "tz": "America/New_York", "locale": "en-US"},
    "United Kingdom": {"base": "https://www.google.co.uk", "gl": "uk", "hl": "en", "tz": "Europe/London", "locale": "en-GB"},
    "Australia": {"base": "https://www.google.com.au", "gl": "au", "hl": "en", "tz": "Australia/Sydney", "locale": "en-AU"},
    "Canada": {"base": "https://www.google.ca", "gl": "ca", "hl": "en", "tz": "America/Toronto", "locale": "en-CA"},
    "Pakistan": {"base": "https://www.google.com.pk", "gl": "pk", "hl": "en", "tz": "Asia/Karachi", "locale": "en-PK"},
    "India": {"base": "https://www.google.co.in", "gl": "in", "hl": "en", "tz": "Asia/Kolkata", "locale": "en-IN"},
    "United Arab Emirates": {"base": "https://www.google.ae", "gl": "ae", "hl": "ar", "tz": "Asia/Dubai", "locale": "ar-AE"},
    "Saudi Arabia": {"base": "https://www.google.com.sa", "gl": "sa", "hl": "ar", "tz": "Asia/Riyadh", "locale": "ar-SA"},
    "Russia": {"base": "https://www.google.ru", "gl": "ru", "hl": "ru", "tz": "Europe/Moscow", "locale": "ru-RU"},
    "Germany": {"base": "https://www.google.de", "gl": "de", "hl": "de", "tz": "Europe/Berlin", "locale": "de-DE"},
    "France": {"base": "https://www.google.fr", "gl": "fr", "hl": "fr", "tz": "Europe/Paris", "locale": "fr-FR"},
    "Spain": {"base": "https://www.google.es", "gl": "es", "hl": "es", "tz": "Europe/Madrid", "locale": "es-ES"},
    "Italy": {"base": "https://www.google.it", "gl": "it", "hl": "it", "tz": "Europe/Rome", "locale": "it-IT"},
    "Brazil": {"base": "https://www.google.com.br", "gl": "br", "hl": "pt-BR", "tz": "America/Sao_Paulo", "locale": "pt-BR"},
    "Netherlands": {"base": "https://www.google.nl", "gl": "nl", "hl": "nl", "tz": "Europe/Amsterdam", "locale": "nl-NL"},
    "Turkey": {"base": "https://www.google.com.tr", "gl": "tr", "hl": "tr", "tz": "Europe/Istanbul", "locale": "tr-TR"},
    "Singapore": {"base": "https://www.google.com.sg", "gl": "sg", "hl": "en", "tz": "Asia/Singapore", "locale": "en-SG"},
    "Japan": {"base": "https://www.google.co.jp", "gl": "jp", "hl": "ja", "tz": "Asia/Tokyo", "locale": "ja-JP"},
    "South Africa": {"base": "https://www.google.co.za", "gl": "za", "hl": "en", "tz": "Africa/Johannesburg", "locale": "en-ZA"},
    "New Zealand": {"base": "https://www.google.co.nz", "gl": "nz", "hl": "en", "tz": "Pacific/Auckland", "locale": "en-NZ"},
    "Ireland": {"base": "https://www.google.ie", "gl": "ie", "hl": "en", "tz": "Europe/Dublin", "locale": "en-IE"},
    "Switzerland": {"base": "https://www.google.ch", "gl": "ch", "hl": "de", "tz": "Europe/Zurich", "locale": "de-CH"},
    "Sweden": {"base": "https://www.google.se", "gl": "se", "hl": "sv", "tz": "Europe/Stockholm", "locale": "sv-SE"},
    "Norway": {"base": "https://www.google.no", "gl": "no", "hl": "no", "tz": "Europe/Oslo", "locale": "nb-NO"},
    "Denmark": {"base": "https://www.google.dk", "gl": "dk", "hl": "da", "tz": "Europe/Copenhagen", "locale": "da-DK"},
    "Finland": {"base": "https://www.google.fi", "gl": "fi", "hl": "fi", "tz": "Europe/Helsinki", "locale": "fi-FI"},
    "Poland": {"base": "https://www.google.pl", "gl": "pl", "hl": "pl", "tz": "Europe/Warsaw", "locale": "pl-PL"},
    "Portugal": {"base": "https://www.google.pt", "gl": "pt", "hl": "pt", "tz": "Europe/Lisbon", "locale": "pt-PT"},
    "Austria": {"base": "https://www.google.at", "gl": "at", "hl": "de", "tz": "Europe/Vienna", "locale": "de-AT"},
    "Belgium": {"base": "https://www.google.be", "gl": "be", "hl": "nl", "tz": "Europe/Brussels", "locale": "nl-BE"},
    "Mexico": {"base": "https://www.google.com.mx", "gl": "mx", "hl": "es", "tz": "America/Mexico_City", "locale": "es-MX"},
    "Argentina": {"base": "https://www.google.com.ar", "gl": "ar", "hl": "es", "tz": "America/Argentina/Buenos_Aires", "locale": "es-AR"},
    "Chile": {"base": "https://www.google.cl", "gl": "cl", "hl": "es", "tz": "America/Santiago", "locale": "es-CL"},
    "Colombia": {"base": "https://www.google.com.co", "gl": "co", "hl": "es", "tz": "America/Bogota", "locale": "es-CO"},
    "Malaysia": {"base": "https://www.google.com.my", "gl": "my", "hl": "ms", "tz": "Asia/Kuala_Lumpur", "locale": "ms-MY"},
    "Indonesia": {"base": "https://www.google.co.id", "gl": "id", "hl": "id", "tz": "Asia/Jakarta", "locale": "id-ID"},
    "Philippines": {"base": "https://www.google.com.ph", "gl": "ph", "hl": "en", "tz": "Asia/Manila", "locale": "en-PH"},
    "Thailand": {"base": "https://www.google.co.th", "gl": "th", "hl": "th", "tz": "Asia/Bangkok", "locale": "th-TH"},
    "Vietnam": {"base": "https://www.google.com.vn", "gl": "vn", "hl": "vi", "tz": "Asia/Ho_Chi_Minh", "locale": "vi-VN"},
    "Egypt": {"base": "https://www.google.com.eg", "gl": "eg", "hl": "ar", "tz": "Africa/Cairo", "locale": "ar-EG"},
    "Nigeria": {"base": "https://www.google.com.ng", "gl": "ng", "hl": "en", "tz": "Africa/Lagos", "locale": "en-NG"},
    "Kenya": {"base": "https://www.google.co.ke", "gl": "ke", "hl": "en", "tz": "Africa/Nairobi", "locale": "en-KE"},
    "Qatar": {"base": "https://www.google.com.qa", "gl": "qa", "hl": "ar", "tz": "Asia/Qatar", "locale": "ar-QA"},
    "Kuwait": {"base": "https://www.google.com.kw", "gl": "kw", "hl": "ar", "tz": "Asia/Kuwait", "locale": "ar-KW"},
    "Oman": {"base": "https://www.google.com.om", "gl": "om", "hl": "ar", "tz": "Asia/Muscat", "locale": "ar-OM"},
    "Bahrain": {"base": "https://www.google.com.bh", "gl": "bh", "hl": "ar", "tz": "Asia/Bahrain", "locale": "ar-BH"},
    "Greece": {"base": "https://www.google.gr", "gl": "gr", "hl": "el", "tz": "Europe/Athens", "locale": "el-GR"},
    "Czech Republic": {"base": "https://www.google.cz", "gl": "cz", "hl": "cs", "tz": "Europe/Prague", "locale": "cs-CZ"},
    "Romania": {"base": "https://www.google.ro", "gl": "ro", "hl": "ro", "tz": "Europe/Bucharest", "locale": "ro-RO"},
    "Hungary": {"base": "https://www.google.hu", "gl": "hu", "hl": "hu", "tz": "Europe/Budapest", "locale": "hu-HU"},
    "South Korea": {"base": "https://www.google.co.kr", "gl": "kr", "hl": "ko", "tz": "Asia/Seoul", "locale": "ko-KR"},
    "Hong Kong": {"base": "https://www.google.com.hk", "gl": "hk", "hl": "zh-TW", "tz": "Asia/Hong_Kong", "locale": "zh-HK"},
    "Taiwan": {"base": "https://www.google.tw", "gl": "tw", "hl": "zh-TW", "tz": "Asia/Taipei", "locale": "zh-TW"},
    "Israel": {"base": "https://www.google.co.il", "gl": "il", "hl": "iw", "tz": "Asia/Jerusalem", "locale": "he-IL"},
    "Morocco": {"base": "https://www.google.co.ma", "gl": "ma", "hl": "ar", "tz": "Africa/Casablanca", "locale": "ar-MA"},
    "Algeria": {"base": "https://www.google.dz", "gl": "dz", "hl": "ar", "tz": "Africa/Algiers", "locale": "ar-DZ"},
    "Bangladesh": {"base": "https://www.google.com.bd", "gl": "bd", "hl": "bn", "tz": "Asia/Dhaka", "locale": "bn-BD"},
    "Sri Lanka": {"base": "https://www.google.lk", "gl": "lk", "hl": "si", "tz": "Asia/Colombo", "locale": "si-LK"},
    "Nepal": {"base": "https://www.google.com.np", "gl": "np", "hl": "ne", "tz": "Asia/Kathmandu", "locale": "ne-NP"},
    "Peru": {"base": "https://www.google.com.pe", "gl": "pe", "hl": "es", "tz": "America/Lima", "locale": "es-PE"},
    "Ukraine": {"base": "https://www.google.com.ua", "gl": "ua", "hl": "uk", "tz": "Europe/Kyiv", "locale": "uk-UA"},
}

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

class RankCheckerThread(QThread):
    status_changed = Signal(str)
    keyword_started = Signal(str, int, int)
    keyword_completed = Signal(dict)
    progress_updated = Signal(int, int)
    captcha_detected = Signal(str)
    captcha_cleared = Signal()
    log_message = Signal(str)
    finished_processing = Signal()

    def __init__(
        self,
        domain: str,
        keywords: List[str],
        country: str,
        max_pages: int,
        state_manager: StateManager,
        proxy_string: str = "",
        scan_mode: str = "single",
        override_timezone: bool = False,
        headless: bool = False
    ):
        super().__init__()
        self.target_domain = self.clean_domain(domain)
        self.keywords = keywords
        self.country_name = country
        self.max_pages = max_pages
        self.state_manager = state_manager
        self.proxy_string = proxy_string.strip()
        self.scan_mode = scan_mode
        self.override_timezone = override_timezone
        self.headless = headless

        self.is_paused = False
        self.is_stopped = False
        self.in_captcha_state = False

    @staticmethod
    def clean_domain(domain: str) -> str:
        d = domain.strip().lower()
        d = re.sub(r'^https?://', '', d)
        d = re.sub(r'^www\.', '', d)
        return d.split('/')[0].split('?')[0]

    def is_domain_match(self, target_domain: str, candidate_url: str) -> bool:
        target = self.clean_domain(target_domain)
        cand_domain = self.clean_domain(candidate_url)
        
        if not target or not cand_domain:
            return False
        
        if target == cand_domain:
            return True
        if cand_domain.endswith("." + target):
            return True
        if target.endswith("." + cand_domain):
            return True
        if target in cand_domain:
            return True
        return False

    @staticmethod
    def resolve_redirect_url(url: str) -> str:
        """
        Fast non-blocking redirect resolver for TARGET DOMAIN only.
        Timeout is capped at 0.8s so it never causes freezes.
        """
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return url

        parsed = urllib.parse.urlparse(url)
        if not any(g in parsed.netloc.lower() for g in ["google.com", "google.ae", "google.co", "google."]):
            return url

        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}
            )
            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            opener = urllib.request.build_opener(NoRedirect)
            try:
                resp = opener.open(req, timeout=0.8)
                return resp.geturl()
            except urllib.error.HTTPError as e:
                if 'Location' in e.headers:
                    return e.headers['Location']
        except Exception:
            pass

        return url

    def parse_proxy(self) -> Optional[Dict[str, str]]:
        if not self.proxy_string:
            return None
        ps = self.proxy_string.strip()
        if not ps.startswith("http://") and not ps.startswith("https://") and not ps.startswith("socks5://"):
            parts = ps.split(":")
            if len(parts) == 2:
                return {"server": f"http://{parts[0]}:{parts[1]}"}
            elif len(parts) == 4:
                return {
                    "server": f"http://{parts[0]}:{parts[1]}",
                    "username": parts[2],
                    "password": parts[3]
                }
        return {"server": ps}

    def pause(self):
        self.is_paused = True
        self.status_changed.emit("Paused")
        self.log_message.emit("[INFO] Processing paused by user.")

    def resume(self):
        self.is_paused = False
        self.in_captcha_state = False
        self.status_changed.emit("Running")
        self.log_message.emit("[INFO] Processing resumed.")

    def stop(self):
        self.is_stopped = True
        self.is_paused = False
        self.in_captcha_state = False
        self.status_changed.emit("Stopped")
        self.log_message.emit("[INFO] Stopping process...")

    def random_delay(self, min_sec: float = 1.0, max_sec: float = 2.0):
        """Ultra-fast safe dynamic delay."""
        sec = random.uniform(min_sec, max_sec)
        time.sleep(sec)

    def check_pause_and_stop(self, page: Optional[Page] = None):
        while self.is_paused or self.in_captcha_state:
            if self.is_stopped:
                break
            time.sleep(0.3)

    def launch_context(self, p, country_info: Dict[str, Any], proxy_dict: Optional[Dict[str, str]]):
        """
        Launches real Chrome/Edge persistent context cleanly.
        """
        user_data_dir = os.path.abspath(os.path.join("data", "browser_profile"))
        os.makedirs(user_data_dir, exist_ok=True)
        
        base_args = [
            "--disable-blink-features=AutomationControlled",
            "--start-maximized",
            "--disable-infobars",
            "--no-first-run",
            "--no-service-autorun",
            "--proxy-auto-detect",
            "--force-webrtc-ip-handling-policy=disable_non_proxied_udp"
        ]

        ext_path = os.path.normpath(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "extensions", "remove_breadcrumbs")))
        if not os.path.exists(ext_path):
            ext_path = os.path.normpath(os.path.abspath(os.path.join("assets", "extensions", "remove_breadcrumbs")))

        if os.path.exists(ext_path):
            base_args.extend([
                f"--disable-extensions-except={ext_path}",
                f"--load-extension={ext_path}"
            ])

        user_agent = random.choice(USER_AGENTS)
        locale = country_info.get("locale", "en-US")
        hl = country_info.get("hl", "en")

        context_kwargs: Dict[str, Any] = {
            "user_data_dir": user_data_dir,
            "headless": self.headless,
            "args": base_args,
            "ignore_default_args": ["--enable-automation"],
            "user_agent": user_agent,
            "viewport": {"width": 1280, "height": 800},
            "locale": locale,
            "extra_http_headers": {
                "Accept-Language": f"{hl},{locale};q=0.9,en;q=0.8"
            }
        }

        if self.override_timezone:
            context_kwargs["timezone_id"] = country_info.get("tz", "America/New_York")

        if proxy_dict:
            context_kwargs["proxy"] = proxy_dict

        try:
            return p.chromium.launch_persistent_context(**context_kwargs, channel="chrome")
        except Exception:
            pass

        try:
            return p.chromium.launch_persistent_context(**context_kwargs, channel="msedge")
        except Exception:
            pass

        return p.chromium.launch_persistent_context(**context_kwargs)

    def run(self):
        try:
            self.status_changed.emit("Running")
            mode_desc = "Single Best Match" if self.scan_mode == "single" else "All Occurrences Across Pages"
            self.log_message.emit(f"[START] Rank checking for domain: '{self.target_domain}' ({len(self.keywords)} keywords) | Mode: {mode_desc} (Ultra-Fast ⚡)")

            country_info = COUNTRY_DOMAINS.get(self.country_name, COUNTRY_DOMAINS["United States"])
            
            tz_status = f"Enabled ({country_info['tz']})" if self.override_timezone else "Disabled (Natural)"
            self.log_message.emit(f"[GEO-TARGETING] Country: {self.country_name} | Locale: {country_info['locale']} | Timezone Emulation: {tz_status}")

            proxy_dict = self.parse_proxy()
            if proxy_dict:
                self.log_message.emit(f"[PROXY] Routing traffic through: {proxy_dict['server']}")

            with sync_playwright() as p:
                context = self.launch_context(p, country_info, proxy_dict)
                page = context.pages[0] if context.pages else context.new_page()

                loc = country_info.get("locale", "en-US")
                hl = country_info.get("hl", "en")

                page.add_init_script(f"""
                    Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
                    window.chrome = {{ runtime: {{}}, app: {{}}, loadTimes: () => {{}}, csi: () => {{}} }};
                    Object.defineProperty(navigator, 'languages', {{ get: () => ['{loc}', '{hl}', 'en'] }});
                    
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({{ state: Notification.permission }}) :
                            originalQuery(parameters)
                    );
                    
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {{
                        if (parameter === 37445) return 'NVIDIA Corporation';
                        if (parameter === 37446) return 'NVIDIA GeForce GTX 1050/PCIe/SSE2';
                        return getParameter.apply(this, [parameter]);
                    }};
                """)

                try:
                    page.goto(country_info["base"], wait_until="domcontentloaded", timeout=15000)
                    time.sleep(0.5)
                except Exception:
                    pass

                completed_map = self.state_manager.get_completed_keywords()
                total_kw = len(self.keywords)
                completed_count = 0

                for idx, keyword in enumerate(self.keywords, start=1):
                    if self.is_stopped:
                        break

                    if self.state_manager.is_keyword_completed(keyword):
                        self.log_message.emit(f"[SKIP] Keyword '{keyword}' already completed. Skipping.")
                        res_list = completed_map.get(keyword, [])
                        if isinstance(res_list, list):
                            for r in res_list:
                                self.keyword_completed.emit(r)
                        else:
                            self.keyword_completed.emit(res_list)
                        completed_count += 1
                        self.progress_updated.emit(completed_count, total_kw)
                        continue

                    self.keyword_started.emit(keyword, idx, total_kw)
                    self.log_message.emit(f"\n[KEYWORD {idx}/{total_kw}] Searching: '{keyword}'")

                    results = self.process_keyword(page, keyword, country_info)
                    
                    if self.is_stopped:
                        break

                    self.state_manager.record_result(keyword, results)
                    for r in results:
                        self.keyword_completed.emit(r)
                    
                    completed_count += 1
                    self.progress_updated.emit(completed_count, total_kw)

                    self.random_delay(1.2, 2.2)

                try:
                    context.close()
                except Exception:
                    pass

            if not self.is_stopped:
                self.status_changed.emit("Completed")
                self.log_message.emit("\n[FINISHED] All keywords processed successfully.")
                
        except Exception as e:
            self.log_message.emit(f"\n[CRITICAL ERROR] Execution failed: {e}")
            self.status_changed.emit("Error")
        finally:
            self.finished_processing.emit()

    def process_keyword(self, page: Page, keyword: str, country_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base_url = country_info["base"]
        gl = country_info["gl"]
        hl = country_info["hl"]

        found_results = []

        for page_num in range(1, self.max_pages + 1):
            if self.is_stopped:
                break

            self.check_pause_and_stop(page)
            if self.is_stopped:
                break

            start_param = (page_num - 1) * 10
            query_params = {
                "q": keyword,
                "gl": gl,
                "hl": hl,
                "pws": "0",
                "start": str(start_param)
            }
            search_url = f"{base_url}/search?{urllib.parse.urlencode(query_params)}"
            
            self.log_message.emit(f"  -> Checking Google Page {page_num}...")
            
            try:
                page.goto(search_url, wait_until="domcontentloaded", timeout=18000)
                time.sleep(0.1)

                if CaptchaHandler.is_captcha_present(page):
                    self.log_message.emit(f"  [!] CAPTCHA / Rate limit detected on page {page_num}.")
                    self.captcha_detected.emit(f"CAPTCHA encountered for '{keyword}' on page {page_num}.")
                    self.status_changed.emit("CAPTCHA REQUIRED")
                    
                    CaptchaHandler.bring_browser_to_front(page)
                    self.in_captcha_state = True
                    
                    while self.in_captcha_state and not self.is_stopped:
                        time.sleep(1.0)
                        try:
                            current_url = page.url.lower()
                            has_search = page.locator("#search, #rso, #center_col, textarea[name='q'], input[name='q']").count() > 0
                            if ("/search" in current_url or has_search) and not CaptchaHandler.is_captcha_present(page):
                                self.log_message.emit("  [+] CAPTCHA cleared! Automatically resuming search...")
                                self.in_captcha_state = False
                                self.captcha_cleared.emit()
                                self.status_changed.emit("Running")
                                break
                        except Exception:
                            pass

                    if self.is_stopped:
                        return [{
                            "keyword": keyword,
                            "domain": self.target_domain,
                            "rank": "N/A",
                            "google_page": "N/A",
                            "ranking_url": "",
                            "target_country": self.country_name,
                            "checked_at": now_str,
                            "status": "CAPTCHA"
                        }]
                    
                    time.sleep(0.5)

                # Instant extraction with 0 delay for non-target links
                organic_links = self.extract_organic_links(page)
                self.log_message.emit(f"    (Found {len(organic_links)} organic results on Page {page_num})")
                
                # Check for target domain matches
                for local_idx, link_info in enumerate(organic_links, start=1):
                    global_rank = (page_num - 1) * 10 + local_idx
                    url = link_info["url"]

                    if self.is_domain_match(self.target_domain, url):
                        self.log_message.emit(f"  [★ FOUND] Domain '{self.target_domain}' found at Rank #{global_rank} (Page {page_num}, Pos {local_idx})!")
                        self.log_message.emit(f"    URL: {url}")
                        
                        match_entry = {
                            "keyword": keyword,
                            "domain": self.target_domain,
                            "rank": global_rank,
                            "google_page": page_num,
                            "ranking_url": url,
                            "target_country": self.country_name,
                            "checked_at": now_str,
                            "status": "Found"
                        }
                        found_results.append(match_entry)

                        if self.scan_mode == "single":
                            return found_results

            except Exception as e:
                self.log_message.emit(f"  [ERROR] Error checking page {page_num}: {e}")
                
            self.random_delay(0.2, 0.4)

        if found_results:
            return found_results
        
        self.log_message.emit(f"  [-] Domain '{self.target_domain}' not found in top {self.max_pages} pages ({self.max_pages * 10} results).")
        return [{
            "keyword": keyword,
            "domain": self.target_domain,
            "rank": "N/A",
            "google_page": "N/A",
            "ranking_url": "",
            "target_country": self.country_name,
            "checked_at": now_str,
            "status": "Not Found"
        }]

    def extract_organic_links(self, page: Page) -> List[Dict[str, str]]:
        """
        Instant 0ms-Delay Organic Link Extractor:
        Extracts all organic results instantly in JavaScript.
        Only resolves 302 redirects for items matching self.target_domain!
        """
        results = []
        seen_urls = set()

        try:
            raw_links = page.evaluate("""
                () => {
                    const results = [];
                    const seenContainers = new Set();
                    
                    const selectors = [
                        '#rso div.MjjYud',
                        '#rso div.g',
                        '#search div.g',
                        'div.yuRUbf',
                        '#rso > div'
                    ];
                    
                    const containers = document.querySelectorAll(selectors.join(', '));
                    
                    containers.forEach(container => {
                        if (seenContainers.has(container)) return;
                        
                        let adParent = container.closest('div[data-text-ad], .uEvd2e, [aria-label*="Sponsored"], [aria-label*="Ads"], .vdL23');
                        if (adParent) return;
                        
                        let text = (container.innerText || '').trim();
                        if (text.startsWith('Sponsored') || text.startsWith('Ad ')) return;
                        
                        const heading = container.querySelector('h3');
                        if (!heading) return;
                        
                        seenContainers.add(container);
                        let title = (heading.innerText || '').trim();
                        
                        const mainAnchor = heading.closest('a') || container.querySelector('a:has(h3)') || container.querySelector('div.yuRUbf > a') || container.querySelector('a[href]');
                        let href = mainAnchor ? (mainAnchor.getAttribute('href') || mainAnchor.href || '') : '';
                        let dataUrl = mainAnchor ? (mainAnchor.getAttribute('data-url') || mainAnchor.getAttribute('data-href') || mainAnchor.getAttribute('data-rw') || '') : '';
                        
                        let directChildUrl = '';
                        const otherAnchors = container.querySelectorAll('a');
                        for (let oa of otherAnchors) {
                            let raw = oa.href || oa.getAttribute('href') || '';
                            if (raw && (raw.startsWith('http://') || raw.startsWith('https://')) && !raw.includes('google.')) {
                                directChildUrl = raw;
                                break;
                            }
                        }

                        const citeEl = container.querySelector('cite') || 
                                       container.querySelector('div.TbwUpd') || 
                                       container.querySelector('span.cite') || 
                                       container.querySelector('span[role="text"]') ||
                                       container.querySelector('div.VwiC3b');
                                       
                        let citeText = citeEl ? (citeEl.innerText || citeEl.textContent || '').trim() : '';

                        if (!citeText) {
                            const possibleSpans = container.querySelectorAll('span, div');
                            for (let s of possibleSpans) {
                                let t = (s.innerText || '').trim();
                                if ((t.includes('http://') || t.includes('https://') || t.includes('.')) && (t.includes('›') || t.includes('>'))) {
                                    citeText = t;
                                    break;
                                }
                            }
                        }

                        results.push({
                            href: href,
                            dataUrl: dataUrl,
                            directChildUrl: directChildUrl,
                            citeText: citeText,
                            title: title,
                            containerText: text.toLowerCase()
                        });
                    });
                    
                    return results;
                }
            """)

            for item in raw_links:
                href = item.get("href", "").strip()
                data_url = item.get("dataUrl", "").strip()
                direct_child = item.get("directChildUrl", "").strip()
                cite_text = item.get("citeText", "").strip()
                title = item.get("title", "").strip()
                container_text = item.get("containerText", "")

                candidate_url = ""

                # 1. Direct child URL (0ms)
                if direct_child:
                    candidate_url = direct_child

                # 2. Check direct links
                if not candidate_url:
                    target_from_link = data_url if (data_url and data_url.startswith("http")) else href

                    if "/url?" in target_from_link or "/goto?" in target_from_link:
                        # Plain query param check (0ms)
                        try:
                            parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(target_from_link).query)
                            for p_name in ["q", "url", "u"]:
                                if p_name in parsed_qs and parsed_qs[p_name]:
                                    val = parsed_qs[p_name][0]
                                    if val.startswith("http://") or val.startswith("https://"):
                                        candidate_url = val
                                        break
                        except Exception:
                            pass

                        # ONLY resolve 302 redirect for our specific target domain (0ms for all other domains!)
                        if not candidate_url:
                            is_our_target = (self.target_domain in container_text or 
                                             self.target_domain in cite_text.lower() or 
                                             self.target_domain in target_from_link.lower())

                            if is_our_target:
                                if target_from_link.startswith("/"):
                                    target_from_link = "https://www.google.com" + target_from_link
                                resolved = self.resolve_redirect_url(target_from_link)
                                if resolved and not any(g in urllib.parse.urlparse(resolved).netloc.lower() for g in ["google.com", "google.ae", "google.co", "google."]):
                                    candidate_url = resolved

                    elif target_from_link.startswith("http://") or target_from_link.startswith("https://"):
                        parsed_domain = urllib.parse.urlparse(target_from_link).netloc.lower()
                        is_google = any(g_dom in parsed_domain for g_dom in ["google.com", "google.co", "googleusercontent.com", "gstatic.com", "youtube.com", "schema.org"])
                        if not is_google:
                            candidate_url = target_from_link

                # 3. Breadcrumb / Cite fallback (0ms)
                if not candidate_url and cite_text:
                    url_match = re.search(r'(https?://[^\s>›]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s>›]*)', cite_text)
                    if url_match:
                        clean_cite_text = re.sub(r'[\s>›]+', '/', cite_text)
                        url_match2 = re.search(r'(https?://[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s]*)', clean_cite_text)
                        if url_match2:
                            raw_cite = url_match2.group(1).strip()
                            if not raw_cite.startswith("http://") and not raw_cite.startswith("https://"):
                                raw_cite = "https://" + raw_cite
                            
                            p_dom = urllib.parse.urlparse(raw_cite).netloc.lower()
                            is_google = any(g_dom in p_dom for g_dom in ["google.com", "google.co", "googleusercontent.com", "gstatic.com", "youtube.com", "schema.org"])
                            if not is_google and len(p_dom) > 3 and "." in p_dom:
                                candidate_url = raw_cite

                if not candidate_url:
                    continue

                clean_href = candidate_url.split("?utm_")[0].split("&utm_")[0].strip()

                if clean_href not in seen_urls:
                    seen_urls.add(clean_href)
                    results.append({"url": clean_href, "title": title})

        except Exception as e:
            self.log_message.emit(f"    [WARN] Exception extracting links: {e}")

        return results
