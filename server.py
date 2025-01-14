from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    try:
        # Save the data to xtream_login.json
        with open("xtream_login.json", "w") as file:
            json.dump(data, file, indent=4)
        return jsonify({"message": "Details saved successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
