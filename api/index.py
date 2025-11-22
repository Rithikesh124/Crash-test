from flask import Flask, jsonify, request
import requests
import json

app = Flask(__name__)

# ==========================================
# ⚠️ PASTE YOUR STAKE ACCESS TOKEN BELOW ⚠️
# ==========================================
HARDCODED_ACCESS_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c" 
# ==========================================

def fetch_stake_crash_history(limit=50):
    """
    Fetches the crash game history from Stake.com
    """
    url = 'https://stake.com/_api/graphql'
    
    # Headers mimicking a real browser to avoid some blocking
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/graphql+json, application/json',
        'x-access-token': HARDCODED_ACCESS_TOKEN,
        'x-language': 'en',
        'Referer': 'https://stake.com/casino/games/crash',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    query = """
        query CrashGameListHistory($limit: Int, $offset: Int) {
            crashGameList(limit: $limit, offset: $offset) {
                crashpoint
            }
        }
    """

    body = {
        'query': query,
        'operationName': "CrashGameListHistory",
        'variables': {
            'limit': limit,
            'offset': 0
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
        response.raise_for_status()
        data = response.json()

        # Check for internal GraphQL errors
        if 'errors' in data:
            return {"error": "Stake GraphQL Error", "details": data['errors']}

        # Extract just the crashpoint numbers
        crash_game_list = data.get('data', {}).get('crashGameList', [])
        crashpoints = [item['crashpoint'] for item in crash_game_list if 'crashpoint' in item]
        
        return {"success": True, "count": len(crashpoints), "crashpoints": crashpoints}

    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "details": str(e)}
    except Exception as e:
        return {"error": "Unknown error", "details": str(e)}

@app.route('/', methods=['GET'])
def home():
    """
    Endpoint to get crash points.
    Usage: GET /?limit=20 (default is 50)
    """
    # Check if token is set
    if not HARDCODED_ACCESS_TOKEN or "PASTE_YOUR" in HARDCODED_ACCESS_TOKEN:
        return jsonify({"error": "Configuration Error", "message": "You must put your Access Token inside api/index.py"}), 500

    # Get limit from URL query, e.g., site.com/?limit=10
    limit_param = request.args.get('limit', default=50, type=int)
    
    # Cap the limit to avoid timeouts/bans
    if limit_param > 100:
        limit_param = 100

    result = fetch_stake_crash_history(limit=limit_param)
    
    if "error" in result:
        return jsonify(result), 500
        
    return jsonify(result), 200

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
