import requests

url = "https://instagram-scraper-api2.p.rapidapi.com/v1/info"
querystring = {"username_or_id_or_url":"drharang"}
headers = {
	"x-rapidapi-key": "SIGN-UP-FOR-KEY",
	"x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
}
try:
    response = requests.get(url, headers=headers, params=querystring)
    print(response.status_code)
except Exception as e:
    pass
