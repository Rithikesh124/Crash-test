from flask import Flask, jsonify
import requests
import json

app = Flask(__name__)

# ====================================================
# ⬇️ PASTE YOUR HARDCODED TOKEN HERE ⬇️
# ====================================================
HARDCODED_ACCESS_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c"
# ====================================================

@app.route('/', methods=['GET'])
def get_crash_points():
    """
    Fetches crash points using the exact headers/query provided.
    """
    
    # 1. URL
    url = 'https://stake.com/_api/graphql'

    # 2. HEADERS (Exact copy from your JS snippet)
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/graphql+json, application/json',
        'x-access-token': HARDCODED_ACCESS_TOKEN,
        'x-language': 'en',
        'Referer': 'https://stake.com/casino/games/crash',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36'
    }

    # 3. GRAPHQL BODY (Exact copy from your JS snippet)
    # We replicate the query structure including id, startTime, etc.
    # to make the request look identical to the one you trust.
    query_string = """
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
        'query': query_string,
        'operationName': "CrashGameListHistory",
        'variables': {
            'limit': 20, # As requested in your snippet
            'offset': 0
        }
    }

    try:
        # Perform the POST request
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # Check if Stake returned a 403/Forbidden or other error
        if response.status_code != 200:
            return jsonify({
                "error": f"Stake returned status code {response.status_code}",
                "details": response.text
            }), response.status_code

        data = response.json()

        # Check for GraphQL errors
        if 'errors' in data:
            return jsonify({"error": "GraphQL Error", "details": data['errors']}), 400

        # 4. EXTRACT ONLY CRASH POINTS (Logic from your JS: item => item.crashpoint)
        crash_game_list = data.get('data', {}).get('crashGameList', [])
        
        if not crash_game_list:
             return jsonify({"message": "No data returned", "crashpoints": []}), 200

        crashpoints = [item['crashpoint'] for item in crash_game_list if 'crashpoint' in item]

        # Return JSON response
        return jsonify({
            "success": True,
            "crashpoints": crashpoints
        })

    except Exception as e:
        return jsonify({"error": "Server Error", "details": str(e)}), 500

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
