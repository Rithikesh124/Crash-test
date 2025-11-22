import os
from flask import Flask, jsonify, request
import requests
import traceback
import json

app = Flask(__name__)

# =======================================================
# ⬇️ PASTE YOUR TOKEN HERE ⬇️
# =======================================================
HARDCODED_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c" 
# =======================================================

# List of domains to try in order
STAKE_DOMAINS = [
    "stake.com",
    "stake.ac",   # Common mirror
    "stake.bet",  # Common mirror
    "stake.games",
    "stake.us"    # Note: Stake.us requires US IP, others block US IP
]

def get_browser_headers(token, domain):
    """
    Generates the headers you see in your browser (Network Tab).
    These are the Client Hints (sec-ch-ua) you asked about.
    """
    return {
        'authority': domain,
        'accept': 'application/graphql+json, application/json',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': f'https://{domain}',
        'referer': f'https://{domain}/casino/games/crash',
        # THIS IS THE SEC-CH-UA (Spoofing Chrome 124 on Windows)
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'x-access-token': token,
        'x-language': 'en'
    }

@app.route('/debug', methods=['GET'])
def show_request_details():
    """
    Shows exactly what headers this server is sending to Stake.
    """
    headers = get_browser_headers("HIDDEN_TOKEN", "stake.com")
    return jsonify({
        "info": "This is what we are sending to Stake:",
        "simulated_ip": "We cannot change the IP via code. It will be the Render Server IP.",
        "headers_being_sent": headers
    })

@app.route('/', methods=['GET'])
def fetch_data():
    logs = [] # To store what happened on every domain attempt
    
    query = """
    query CrashGameListHistory($limit: Int, $offset: Int) {
        crashGameList(limit: $limit, offset: $offset) {
            crashpoint
        }
    }
    """
    payload = {
        'query': query,
        'operationName': 'CrashGameListHistory',
        'variables': {'limit': 20, 'offset': 0}
    }

    # --- LOOP THROUGH DOMAINS ---
    for domain in STAKE_DOMAINS:
        url = f"https://{domain}/_api/graphql"
        headers = get_browser_headers(HARDCODED_TOKEN, domain)
        
        try:
            # We use a session to mimic a browser connection state
            with requests.Session() as s:
                response = s.post(url, headers=headers, json=payload, timeout=8)
            
            # If successful (200 OK)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and 'crashGameList' in data['data']:
                    games = data['data']['crashGameList']
                    points = [g.get('crashpoint') for g in games]
                    
                    return jsonify({
                        "success": True,
                        "working_domain": domain,
                        "crashpoints": points,
                        "attempt_logs": logs
                    })
                else:
                    logs.append(f"{domain}: 200 OK but invalid JSON structure.")
            
            # If 403 Forbidden
            elif response.status_code == 403:
                logs.append(f"{domain}: 403 Forbidden (Cloudflare blocked IP/Headers).")
            
            else:
                logs.append(f"{domain}: Status {response.status_code} - {response.text[:50]}")

        except Exception as e:
            logs.append(f"{domain}: Error - {str(e)}")

    # If the loop finishes and nothing worked:
    return jsonify({
        "success": False,
        "error": "All domains failed.",
        "analysis": "This likely means the Render Server IP is completely blacklisted by Cloudflare, or the TLS fingerprint of Python requests is detected.",
        "detailed_logs": logs
    }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
