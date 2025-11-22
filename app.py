import os
from flask import Flask, jsonify
import requests
import traceback

app = Flask(__name__)

# =======================================================
# ⬇️ PASTE YOUR TOKEN HERE ⬇️
# =======================================================
HARDCODED_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c"
# =======================================================

@app.route('/', methods=['GET', 'POST'])
def fetch_stake_data():
    try:
        # Headers mimicking a real browser (Crucial for Stake)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/graphql+json, application/json',
            'x-access-token': HARDCODED_TOKEN,
            'x-language': 'en',
            'Referer': 'https://stake.com/casino/games/crash',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
        }

        # The GraphQL Query
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

        # Send Request to Stake
        # We use a session and a slightly longer timeout for stability
        with requests.Session() as s:
            response = s.post('https://stake.com/_api/graphql', headers=headers, json=payload, timeout=10)

        # DEBUG: Check if Stake blocked the specific Region IP
        if response.status_code == 403:
            return jsonify({
                "error": "403 Forbidden",
                "message": "Stake blocked this Render Server Region.",
                "tip": "Try creating a new Render service in a different region (e.g., Singapore or Frankfurt)."
            }), 403

        if response.status_code != 200:
             return jsonify({"error": f"Stake Error {response.status_code}", "body": response.text}), response.status_code

        data = response.json()

        # Parse the data
        if 'data' in data and 'crashGameList' in data['data']:
            games = data['data']['crashGameList']
            # Extract points, handle missing keys safely
            crashpoints = [item.get('crashpoint') for item in games if item.get('crashpoint') is not None]
            
            return jsonify({
                "success": True, 
                "count": len(crashpoints), 
                "crashpoints": crashpoints
            })

        return jsonify({"error": "Invalid Data Structure", "raw_data": data}), 500

    except Exception as e:
        return jsonify({"error": "Internal Server Error", "details": str(e), "trace": traceback.format_exc()}), 500

# This block allows Render to assign the PORT automatically
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
