import json
import os
from typing import List, Dict, Any, Optional, Union

class StateManager:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.state_file = os.path.join(self.storage_dir, "session_progress.json")
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    st = json.load(f)
                    # Purge any old corrupted question-mark keywords from state
                    results = st.get("results", [])
                    if any("??" in r.get("keyword", "") for r in results):
                        st["results"] = []
                        st["completed_keywords"] = {}
                    return st
            except Exception:
                pass
        return {
            "target_domain": "",
            "target_country": "",
            "csv_path": "",
            "proxy": "",
            "max_pages": 5,
            "scan_mode": "single",
            "override_timezone": False,
            "completed_keywords": {},
            "results": []
        }

    def init_session(self, domain: str, country: str, csv_path: str, max_pages: int, proxy: str = "", scan_mode: str = "single", override_timezone: bool = False):
        if (self.state.get("target_domain") != domain or 
            self.state.get("csv_path") != csv_path):
            self.state = {
                "target_domain": domain,
                "target_country": country,
                "csv_path": csv_path,
                "proxy": proxy,
                "max_pages": max_pages,
                "scan_mode": scan_mode,
                "override_timezone": override_timezone,
                "completed_keywords": {},
                "results": []
            }
            self.save_state()
        else:
            self.state["target_country"] = country
            self.state["max_pages"] = max_pages
            self.state["proxy"] = proxy
            self.state["scan_mode"] = scan_mode
            self.state["override_timezone"] = override_timezone
            self.save_state()

    def is_keyword_completed(self, keyword: str) -> bool:
        return keyword in self.state.get("completed_keywords", {})

    def record_result(self, keyword: str, results: Union[Dict[str, Any], List[Dict[str, Any]]]):
        res_list = results if isinstance(results, list) else [results]
        completed = self.state.setdefault("completed_keywords", {})
        completed[keyword] = res_list
        
        # Remove old results for this keyword and add new ones
        self.state["results"] = [r for r in self.state.get("results", []) if r.get("keyword") != keyword]
        self.state["results"].extend(res_list)
        self.save_state()

    def save_state(self):
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving state: {e}")

    def get_results(self) -> List[Dict[str, Any]]:
        return self.state.get("results", [])

    def get_completed_keywords(self) -> Dict[str, Union[Dict[str, Any], List[Dict[str, Any]]]]:
        return self.state.get("completed_keywords", {})

    def reset_state(self):
        self.state = {
            "target_domain": "",
            "target_country": "",
            "csv_path": "",
            "proxy": "",
            "max_pages": 5,
            "scan_mode": "single",
            "override_timezone": False,
            "completed_keywords": {},
            "results": []
        }
        if os.path.exists(self.state_file):
            try:
                os.remove(self.state_file)
            except Exception:
                pass
