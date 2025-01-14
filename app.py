from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400

    try:
        with open('xtream_login.json', 'w') as file:
            json.dump(data, file, indent=4)
        return jsonify({"message": "Credentials updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
