import requests
from bs4 import BeautifulSoup
url = "https://www.picuki.com/profile/drharang"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
resp = requests.get(url, headers=headers)
print(resp.status_code)
if resp.status_code == 200:
    soup = BeautifulSoup(resp.text, 'html.parser')
    for item in soup.select('.box-photo')[:2]:
        link_elem = item.select_one('a')
        if link_elem:
            link = link_elem.get('href', '')
        else:
            link = ''
        img_elem = item.select_one('.post-image')
        if img_elem:
            img = img_elem.get('src', '')
        else:
            img = ''
        print(link, img)
