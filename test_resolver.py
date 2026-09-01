import urllib.request
import urllib.error

def resolve_url(url: str) -> str:
    """
    Follows redirect (or extracts 302 Location header) to return the full, unmasked destination URL.
    """
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        return url

    # If it's already a non-google direct URL, return it
    if "google.com/goto" not in url and "google." not in url:
        return url

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'}
        )
        # Using a custom opener that catches redirects immediately without downloading body
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        opener = urllib.request.build_opener(NoRedirect)
        try:
            resp = opener.open(req, timeout=3)
            return resp.geturl()
        except urllib.error.HTTPError as e:
            if 'Location' in e.headers:
                return e.headers['Location']
    except Exception as e:
        print("Resolve error:", e)
    
    return url

print("Resolver function ready!")
