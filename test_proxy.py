import os
import instaloader
from fp.fp import FreeProxy

proxy = FreeProxy(rand=True, timeout=1).get()
print("Proxy found:", proxy)

L = instaloader.Instaloader()
L.context._session.proxies = {"http": proxy, "https": proxy}

try:
    profile = instaloader.Profile.from_username(L.context, "drharang")
    for post in profile.get_posts():
        print("Success!", post.url)
        break
except Exception as e:
    print("Error:", e)
