import requests
import xml.etree.ElementTree as ET

url = "https://rsshub.app/instagram/user/drharang"
try:
    resp = requests.get(url, timeout=10)
    print("Status:", resp.status_code)
    print("Body preview:", resp.text[:200])
except Exception as e:
    print("Error:", e)
