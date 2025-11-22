from flask import Flask, jsonify, request
import requests
import traceback

app = Flask(__name__)

# YOUR TOKEN
HARDCODED_TOKEN = "684655d7eb7fa4b39ef670d442b79e019433b1aec861d0c2336c27f918c062ad99649121eb15d1303491ff0d0d2da67c"

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "Server is running!", "libs": "Flask/Requests installed correctly"})

@app.route('/', methods=['GET', 'POST'])
def home():
    try:
        # Headers exactly as requested
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/graphql+json, application/json',
            'x-access-token': HARDCODED_TOKEN,
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

        payload = {
            'query': query,
            'operationName': 'CrashGameListHistory',
            'variables': {'limit': 20, 'offset': 0}
        }

        # Send Request
        response = requests.post('https://stake.com/_api/graphql', headers=headers, json=payload, timeout=9)

        # Handle 403 Forbidden specifically
        if response.status_code == 403:
            return jsonify({
                "error": "Forbidden",
                "message": "Stake.com is blocking Vercel's IP address. This code works in Termux because Termux uses your phone's IP.",
                "solution": "You cannot host this on Vercel. You must host it on a VPS (DigitalOcean/Linode) or keep running it locally."
            }), 403

        response.raise_for_status()
        data = response.json()

        # Extract points
        if 'data' in data and 'crashGameList' in data['data']:
            games = data['data']['crashGameList']
            # Safely get crashpoint, default to 0.0 if missing
            points = [g.get('crashpoint', 0.0) for g in games]
            return jsonify({"success": True, "crashpoints": points})

        return jsonify({"error": "Unknown Data Format", "data": data}), 500

    except Exception as e:
        return jsonify({"error": "Internal Error", "details": str(e), "trace": traceback.format_exc()}), 500

# Local start
if __name__ == '__main__':
    app.run(debug=True)
