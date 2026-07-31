from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

CJ_API_KEY = os.environ.get("CJ_API_KEY", "VOTRE_CLE_API_CJ")

def get_cj_access_token():
    url = "https://developers.cjdropshipping.com/api2.0/v1/authentication/getAccessToken"
    headers = {"Content-Type": "application/json"}
    payload = {"apiKey": CJ_API_KEY}
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("result"):
                return data.get("data", {}).get("accessToken")
    except Exception:
        pass
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/calculer-livraison', methods=['GET'])
def api_calculer_livraison():
    vid = request.args.get('vid')
    country = request.args.get('country')
    
    if not vid or not country:
        return jsonify({"success": False, "error": "Paramètres manquants"}), 400

    token = get_cj_access_token()
    if not token:
        return jsonify({"success": False, "error": "Token CJ invalide"}), 500

    url = "https://developers.cjdropshipping.com/api2.0/v1/logistic/freightCalculate"
    headers = {
        "Content-Type": "application/json",
        "CJ-Access-Token": token
    }
    payload = {
        "startCountryCode": "CN",
        "endCountryCode": country,
        "products": [{"quantity": 1, "vid": vid}]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if data.get("success") and data.get("data") and len(data["data"]) > 0:
            # Récupération dynamique du véritable prix de transport CJ
            price = data["data"][0].get("logisticPrice", 0)
            return jsonify({"success": True, "logisticPrice": float(price)})
    except Exception:
        pass

    return jsonify({"success": False, "logisticPrice": 5.00})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
