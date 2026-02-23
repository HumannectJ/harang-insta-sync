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
        # Print a snippet of the posts if available
        if isinstance(data, list):
            print(f"Got {len(data)} items. First item keys: {data[0].keys() if len(data)>0 else 'empty'}")
        elif isinstance(data, dict):
            # Try to guess structure
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"List found under '{k}' with {len(v)} items")
                    if len(v) > 0 and isinstance(v[0], dict):
                        print(f"First item keys: {v[0].keys()}")
    else:
        print("Error Response:", response.text)
except Exception as e:
    print(f"Request failed: {e}")
