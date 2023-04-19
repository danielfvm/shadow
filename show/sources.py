from zipfile import ZipFile

import urllib.request
import random
import string
import os

# The url to a list of all public and verified wallpapers on github
SOURCE_URL = "https://raw.githubusercontent.com/danielfvm/Show/master/requirements.txt"

def get_sources() -> list[str] | None:
    try:
        fs = urllib.request.urlopen(SOURCE_URL)
        content = fs.read().decode("utf8")
        fs.close()

        return content.split('\n')
    except:
        return None

# e.g. https://github.com/danielfvm/Show -> https://raw.githubusercontent.com/danielfvm/Show/master/README.md
def get_preview(source: str) -> str | None:
    url = source.replace("github.com", "raw.githubusercontent.com") + "/master/README.md"

    try:
        fs = urllib.request.urlopen(url)
        content = fs.read().decode("utf8")
        fs.close()

        return content
    except:
        return None

# e.g. https://github.com/danielfvm/Show -> https://github.com/danielfvm/Show/archive/refs/heads/master.zip
def download(source: str, dest: str) -> bool:
    url = source + "/archive/refs/heads/master.zip"
    samples = string.ascii_letters+string.digits
    temp = ''.join(random.sample(samples, 10)) + ".zip"

    try:
        urllib.request.urlretrieve(url, temp)
        with ZipFile(temp) as zFile:
            zFile.extractall(dest)
            zFile.close()
        if os.path.isfile(temp):
            os.remove(temp)

        return True
    except:
        return False


print(download("https://github.com/danielfvm/Show", "test"))
