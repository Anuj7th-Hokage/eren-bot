import urllib.request
def download_meow():
    req = urllib.request.Request(
        "https://www.myinstants.com/media/sounds/meow.mp3", 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req) as response, open("meow.mp3", 'wb') as out_file:
        out_file.write(response.read())

download_meow()
import os
print("File size:", os.path.getsize("meow.mp3"))
