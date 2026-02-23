import requests

key = "ef7b2613ebmshc2f08aa3cb566ecp1354cejsna2132531f647"
host = "instagram-scraper-stable-api.p.rapidapi.com"
endpoints = [
    "/ig_user_medias_v2.php",
    "/get_ig_medias.php",
    "/get_user_profile.php",
    "/get_ig_user_info.php",
    "/get_ig_user_medias.php",
    "/get_ig_user_medias_v2.php",
    "/get_user_posts.php",
    "/user.php",
    "/user_medias.php"
]

for endpoint in endpoints:
    url = f"https://{host}{endpoint}"
    querystring = {"user_name": "drharang", "username": "drharang"}
    headers = {"x-rapidapi-key": key, "x-rapidapi-host": host}
    try:
        res = requests.get(url, headers=headers, params=querystring)
        print(f"{endpoint}: {res.status_code}")
        if res.status_code == 200:
            print("FOUND!", list(res.json().keys()))
    except Exception as e:
        print(e)
