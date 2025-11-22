from flask import Flask, jsonify
import requests
import json

app = Flask(__name__)

# =======================================================
# ⬇️ PASTE THE TOKEN THAT WORKS IN TERMUX HERE ⬇️
# =======================================================
HARDCODED_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c" 
# =======================================================

@app.route('/', methods=['GET'])
def handler():
    # 1. Exact Headers from your bos.py
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/graphql+json, application/json',
        'x-access-token': HARDCODED_TOKEN,
        'x-language': 'en',
        'Referer': 'https://stake.com/casino/games/crash',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    # 2. Exact GraphQL Query from your bos.py
    query = """
    query CrashGameListHistory($limit: Int, $offset: Int) {
        crashGameList(limit: $limit, offset: $offset) {
            id
            startTime
            crashpoint
            hash {
                id
                hash
                __typename
            }
            __typename
        }
    }
    """

    payload = {
        'query': query,
        'operationName': 'CrashGameListHistory',
        'variables': {
            'limit': 20,
            'offset': 0
        }
    }

    try:
        # 3. Request Logic
        url = 'https://stake.com/_api/graphql'
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # Check for non-200 status (like 403 Forbidden)
        if response.status_code != 200:
             return jsonify({
                 "error": f"Stake Request Failed: {response.status_code}", 
                 "details": response.text
             }), response.status_code

        data = response.json()
        
        # 4. Parsing Logic
        if 'data' in data and 'crashGameList' in data['data']:
            crash_game_list = data['data']['crashGameList']
            crashpoints = [item['crashpoint'] for item in crash_game_list]
            
            # Return JSON so your other projects can use it
            return jsonify({
                "success": True,
                "crashpoints": crashpoints
            })
        else:
            return jsonify({"error": "Unexpected Data Structure", "raw": data}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request Exception", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Server Error", "details": str(e)}), 500

# Local testing
if __name__ == '__main__':
    app.run(debug=True)
