import urllib.request
import urllib.parse
import json

def make_web_request(url: str, params: dict = None, method: str = "GET") -> dict:
    """
    A 'Pure Python' helper for making web requests using urllib.
    Simplifies query parameters, JSON decoding, and standard error handling.
    """
    if params:
        query_string = urllib.parse.urlencode(params)
        url = f"{url}?{query_string}"
    
    req = urllib.request.Request(url, method=method)
    req.add_header('User-Agent', 'Mozilla/5.0 (Fissure AEC Agent)')
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode('utf-8')
            return json.loads(res_body)
    except Exception as e:
        return {"error": f"Web request failed: {str(e)}"}
