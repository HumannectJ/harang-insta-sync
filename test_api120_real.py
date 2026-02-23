import requests

url = "https://instagram120.p.rapidapi.com/api/instagram/posts"
payload = {"username": "drharang", "maxId": ""}
headers = {
    "x-rapidapi-key": "ef7b2613ebmshc2f08aa3cb566ecp1354cejsna2132531f647",
    "x-rapidapi-host": "instagram120.p.rapidapi.com",
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Success! Keys in response:", data.keys())
        import json
        with open("instagram120_sample.json", "w") as f:
            json.dump(data, f, indent=2)
except Exception as e:
    print(f"Request failed: {e}")
