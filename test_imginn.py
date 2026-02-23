import requests
from bs4 import BeautifulSoup
url = "https://imginn.com/drharang/"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
resp = requests.get(url, headers=headers)
print("Imginn Status:", resp.status_code)
if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    for item in soup.select('.item')[:2]:
        print(item.text.strip()[:50])
