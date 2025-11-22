import os
import requests
import traceback
from flask import Flask, jsonify

app = Flask(__name__)

# =======================================================
# ⬇️ PASTE YOUR TOKEN HERE ⬇️
# =======================================================
HARDCODED_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c"
# =======================================================

# List of domains to try (Priority Order)
# Note: stake.us uses a different account system, but we include it as requested.
STAKE_DOMAINS = [
    "stake.com",      # Main Global
    "stake.ac",       # Common Mirror
    "stake.games",    # Mirror
    "stake.bet",      # Mirror
    "staketr.com",    # Turkey Mirror
    "stake.us",       # US Only (Likely 401 Unauthorized with a .com token)
    "stake.jp"        # Japan Mirror
]

def analyze_403_reason(response_text, headers):
    """
    Helper to guess why the request was blocked.
    """
    text = response_text.lower()
    
    if "cloudflare" in text:
        return "Blocked by Cloudflare WAF (Bot Detection)"
    if "location" in text or "country" in text or "region" in text:
        return "Geo-Blocked (Region not allowed)"
    if "vpn" in text or "proxy" in text:
        return "Blocked due to Datacenter/VPN IP"
    if "just a moment" in text:
        return "Cloudflare JavaScript Challenge (JS Challenge)"
    
    # Check headers for Cloudflare specific rays
    if 'cf-ray' in headers:
        return f"Cloudflare Ray ID: {headers['cf-ray']} (General Block)"
        
    return "Unknown 403 Forbidden Reason"

@app.route('/', methods=['GET', 'POST'])
def fetch_any_stake_mirror():
    
    debug_report = {} # To store why each domain failed
    success_data = None
    working_domain = None

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
        try:
            url = f"https://{domain}/_api/graphql"
            
            # Dynamic Headers per Domain
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/graphql+json, application/json',
                'x-access-token': HARDCODED_TOKEN,
                'x-language': 'en',
                'Origin': f'https://{domain}',
                'Referer': f'https://{domain}/casino/games/crash',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
            }

            # Send Request (Short timeout to fail fast)
            with requests.Session() as s:
                response = s.post(url, headers=headers, json=payload, timeout=5)

            # 1. SUCCESS CASE
            if response.status_code == 200:
                data = response.json()
                # Validate structure
                if 'data' in data and 'crashGameList' in data['data']:
                    crash_list = data['data']['crashGameList']
                    crashpoints = [item.get('crashpoint') for item in crash_list if item.get('crashpoint')]
                    
                    success_data = crashpoints
                    working_domain = domain
                    break # Stop looping, we found a working one!
                else:
                    debug_report[domain] = f"Status 200, but invalid JSON: {str(data)[:100]}"

            # 2. 403 FORBIDDEN CASE (Analyze why)
            elif response.status_code == 403:
                reason = analyze_403_reason(response.text, response.headers)
                debug_report[domain] = f"403 Forbidden - {reason}"

            # 3. 401 UNAUTHORIZED (Token invalid for this specific domain)
            elif response.status_code == 401:
                debug_report[domain] = "401 Unauthorized (Token invalid for this specific domain/region)"
            
            # 4. OTHER ERRORS
            else:
                debug_report[domain] = f"Status {response.status_code}"

        except requests.exceptions.ConnectionError:
            debug_report[domain] = "Connection Failed (DNS or Host Unreachable)"
        except Exception as e:
            debug_report[domain] = f"Script Error: {str(e)}"

    # --- FINAL RESPONSE ---
    
    if success_data:
        # If we found a working domain, return the data
        return jsonify({
            "success": True,
            "source": f"Fetched successfully via {working_domain}",
            "crashpoints": success_data
        })
    else:
        # If ALL failed, return the detailed debug report
        return jsonify({
            "success": False,
            "message": "All Stake mirrors blocked this request.",
            "debug_report": debug_report,
            "hosting_advice": "Render/AWS IPs are being detected as 'Datacenter'. Try deploying to a region like Singapore or Frankfurt, or run locally."
        }), 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
