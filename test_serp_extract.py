import urllib.parse
import os
import time
from playwright.sync_api import sync_playwright

def test():
    with sync_playwright() as p:
        user_data_dir = os.path.abspath(os.path.join("data", "browser_profile"))
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.pages[0] if context.pages else context.new_page()
        url = 'https://www.google.com/search?q=' + urllib.parse.quote('hudayriyat villas') + '&gl=ae&hl=en&pws=0'
        page.goto(url, wait_until='domcontentloaded')
        time.sleep(2)
        print("Page URL:", page.url)
        print("Page Title:", page.title())
        
        # Check if consent / captcha
        print("H3 count:", page.locator("h3").count())
        for i in range(min(5, page.locator("h3").count())):
            h3_text = page.locator("h3").nth(i).inner_text()
            print(f"H3 #{i+1}:", h3_text)

        context.close()

if __name__ == '__main__':
    test()
