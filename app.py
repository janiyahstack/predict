from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import os

app = Flask(__name__)
CORS(app)

ATTOM_KEY = "ab622c892cea2178fa6fd6d452bf7d82"

def classify_property(prop):
    try:
       address = prop.get("address", {}).get("oneLine", "Unknown")
       year_built = prop.get("summary", {}).get("yearbuilt", 0) or 0
       beds = prop.get("building", {}).get("rooms", {}).get("beds", 0) or 0
       sqft = prop.get("building", {}).get("size", {}).get("universalsize", 0) or 0
       assessed = prop.get("assessment", {}).get("assessed", {}).get("assdttlvalue", 0) or 0

       age = (2026 - year_built) if year_built > 0 else 0

       if age > 40 and sqft > 1200:
         risk = "High Risk"
       elif age > 20 and sqft > 1500:
        risk = "At Risk"
       else:
        risk = "Stable"

       return {
    "address": address,
    "assessed_value": assessed,
    "year_built": year_built,
    "bedrooms": beds,
    "sqft": sqft,
    "risk": risk
}
    except:
     return None

@app.route("/predict", methods=["GET"])
def predict():
    zipcode = request.args.get("zip")
    if not zipcode:
        return jsonify({"error": "zip code required"}), 400

    url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/snapshot"
    headers = {"apikey": ATTOM_KEY, "Accept": "application/json"}
    params = {"postalcode": zipcode, "pagesize": 20}

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return jsonify({"error": "ATTOM API error", "details": response.text}), 500
    
    data = response.json()
    properties = data.get("property", [])

    results = []
    for prop in properties:
        classified = classify_property(prop)
        if classified:
            results.append(classified)

    high = [r for r in results if r["risk"] == "High Risk"]
    at_risk = [r for r in results if r["risk"] == "At Risk"]
    stable = [r for r in results if r["risk"] == "Stable"]

    return jsonify({
        "zip": zipcode,
        "total": len(results),
        "summary": {
            "high_risk": len(high),
            "at_risk": len(at_risk),
            "stable": len(stable)
        },
        "properties": results
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=False)