import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

class CaptchaHandler:
    @staticmethod
    def is_captcha_present(page: Page) -> bool:
        """
        Checks if the current Playwright page is displaying a Google CAPTCHA or Bot Block.
        """
        try:
            url = page.url.lower()
            if "/sorry/" in url:
                return True
            
            # Check if captcha form or turnstile or recaptcha frame is present & visible
            selectors = [
                "#captcha-form",
                "form[action*='SorryRedirect']",
                "iframe[src*='recaptcha']",
                "iframe[src*='google.com/recaptcha']",
                ".g-recaptcha",
                "#recaptcha",
                "div.g-recaptcha"
            ]
            
            for selector in selectors:
                if page.locator(selector).count() > 0:
                    return True
                    
            title = page.title().lower()
            if "sorry..." in title or "unusual traffic" in title:
                return True
                
        except Exception as e:
            logger.debug(f"Error checking CAPTCHA presence: {e}")
            
        return False

    @staticmethod
    def bring_browser_to_front(page: Page):
        """
        Brings the browser page/window to the foreground for manual interaction.
        """
        try:
            page.bring_to_front()
        except Exception as e:
            logger.warning(f"Could not bring page to front: {e}")
