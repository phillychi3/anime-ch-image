import json
import zipfile
import requests

from bs4 import BeautifulSoup
from fuzzywuzzy import process
from urllib.parse import unquote

header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
}

anidb_cache = []


def search_anidb_from_title(title:str):
    """
    search anidb id from title
    """
    global anidb_cache
    if not anidb_cache:
        get_anidb_id()
    result = process.extractOne(title, [x[3] for x in anidb_cache])
    return anidb_cache[[x[3] for x in anidb_cache].index(result[0])][0]

def get_info_from_anidb(id):
    r = requests.get(f"http://api.anidb.net:9001/httpapi?request=anime&client={str}&clientver={int}&aid=17773")

def get_anidb_id():
    """
    one day only can request 1 time
    """
    # r = requests.get("http://anidb.net/api/anime-titles.dat.gz")
    # with open("anime-titles.xml.gz", "wb") as f:
    #     f.write(r.content)
    # with zipfile.ZipFile("anime-titles.xml.gz", "r") as zip_ref:
    #     zip_ref.extractall("anime-titles.xml")
    with open("anime-titles.dat", "r", encoding="utf-8") as f:
        data = []
        for line in f:
            if line.startswith("#"):
                continue
            # <aid>|<type>|<language>|<title>
            if line.split("|")[2] == "zh-Hans":
                temp = line.split("|")
                temp[3] = temp[3].replace("\n", "").strip()
                data.append(temp)
    global anidb_cache
    anidb_cache = data

def from_acggamer(keyword):
    """
    使用巴哈搜尋資料
    由於使用google服務， 需要proxy
    """
    r = requests.get(
        f"https://cse.google.com/cse/element/v1?rsz=10&num=10&hl=zh-TW&source=gcsc&gss=.tw&cselibv=8435450f13508ca1&cx=partner-pub-9012069346306566%3Akd3hd85io9c&q={keyword}+more%3A%E6%89%BE%E4%BD%9C%E5%93%81&safe=active&cse_tok=AB-tC_6VMyQtkrLpd_OErEMPcBI-%3A1712904578463&sort=&exp=cc&callback=google.search.cse.api6738",
        headers=header
    )
    print(r.status_code)
    print(r.text)
    if r.status_code != 200:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    data = json.loads(soup.text.split("(")[1].split(")")[0])
    if data["results"]:
        for item in data["results"]:
            print(item["titleNoFormatting"], unquote(item["url"]))


get_anidb_id()
print(search_anidb_from_title("刀劍神域 Alicization"))