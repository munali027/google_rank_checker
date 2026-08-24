import csv
import os
from typing import List, Dict, Any

class CSVHandler:
    @staticmethod
    def load_keywords(file_path: str) -> List[str]:
        """
        Reads keywords from a CSV or TXT file with multi-encoding support
        (UTF-8, UTF-8-BOM, UTF-16, CP1256/Arabic, CP1252, etc.) and deduplicates
        them preserving original order.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        raw_bytes = None
        with open(file_path, mode='rb') as f:
            raw_bytes = f.read()

        if not raw_bytes:
            return []

        # List of candidate encodings for universal multi-lingual support
        encodings_to_try = [
            'utf-8-sig',
            'utf-8',
            'utf-16',
            'utf-16-le',
            'utf-16-be',
            'cp1256',  # Arabic Windows
            'cp1252',  # Western Europe Windows
            'latin-1',
            'iso-8859-1'
        ]

        text_content = None
        for enc in encodings_to_try:
            try:
                text_content = raw_bytes.decode(enc)
                break
            except (UnicodeDecodeError, ValueError):
                continue

        if text_content is None:
            text_content = raw_bytes.decode('utf-8', errors='replace')

        lines = [line for line in text_content.splitlines() if line.strip()]
        if not lines:
            return []

        keywords = []
        seen = set()

        # Check if line 1 is a header
        first_line_parts = [p.strip().lower() for p in lines[0].split(',')]
        start_idx = 0
        col_idx = 0
        
        if any(h in first_line_parts for h in ['keyword', 'keywords', 'query', 'queries', 'term', 'terms']):
            start_idx = 1
            for idx, part in enumerate(first_line_parts):
                if part in ['keyword', 'keywords', 'query', 'queries', 'term', 'terms']:
                    col_idx = idx
                    break

        for i in range(start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            
            parts = [p.strip().strip('"').strip("'") for p in line.split(',')]
            if len(parts) > col_idx and parts[col_idx]:
                kw = parts[col_idx]
            else:
                kw = parts[0]
            
            if kw and kw not in seen:
                seen.add(kw)
                keywords.append(kw)
                    
        return keywords

    @staticmethod
    def export_results(results: List[Dict[str, Any]], output_path: str, scan_mode: str = "single") -> None:
        """
        Exports rank checking results to CSV matching the specified schema with UTF-8 BOM
        encoding so Excel & all spreadsheet readers render Arabic, Urdu, Chinese & non-ASCII text natively.
        """
        fieldnames = [
            "Keyword",
            "Domain",
            "Rank",
            "Google Page",
            "Ranking URL",
            "Target Country",
            "Checked At",
            "Status"
        ]
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, mode='w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            seen_keywords_in_export = set()
            for res in results:
                kw = res.get("keyword", "")
                
                display_kw = kw
                if scan_mode == "multiple":
                    if kw in seen_keywords_in_export:
                        display_kw = "" # Show keyword name only once on first row
                    else:
                        seen_keywords_in_export.add(kw)

                writer.writerow({
                    "Keyword": display_kw,
                    "Domain": res.get("domain", ""),
                    "Rank": res.get("rank", "N/A"),
                    "Google Page": res.get("google_page", "N/A"),
                    "Ranking URL": res.get("ranking_url", ""),
                    "Target Country": res.get("target_country", ""),
                    "Checked At": res.get("checked_at", ""),
                    "Status": res.get("status", "")
                })
