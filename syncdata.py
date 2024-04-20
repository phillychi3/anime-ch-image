import os
import re
import json
import gzip
import shutil
import aiohttp
import requests
import asyncio

from dotenv import load_dotenv
from bs4 import BeautifulSoup
from fuzzywuzzy import process
from urllib.parse import unquote, quote

# 抓取順序
# anidb > bangumi > acggamer > myanimelist

load_dotenv()
header = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
}

anidb_cache = []
clientname = os.getenv("ANIDB_CLIENT_NAME")
animelistauth = os.getenv("ANIMELIST_AUTH")

async def search_bangumi_from_title(title:str):
    """
    search bangumi id from title
    """
    header = {
        "User-Agent": "phillychi3/anime-ch-image",
        "Accept": "application/json",
        "Cookie": "chii_searchDateLine=1713520746"
    }
    async with aiohttp.ClientSession(headers=header) as session:
        await asyncio.sleep(2)
        async with session.get(f"https://api.bgm.tv/search/subject/{quote(title)}?type=2&responseGroup=small&max_results=4") as r:
            if r.status != 200:
                return None
            data = await r.json()
            if "code" in data and data["code"] != 200:
                return None
        if not data["list"]:
            return None
        data = data["list"][0]["images"]["large"]
        return data

async def search_myanimelist_from_title(title:str,limit:int):
    header = {
        "X-MAL-CLIENT-ID": animelistauth
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.myanimelist.net/v2/anime?q={title}&limit={limit}", headers=header) as r:
            if r.status != 200:
                return None
            data = await r.json()
            if not data["data"]:
                return None
            data = data["data"][0]["node"]["main_picture"]["large"]
            return data

def search_anidb_from_title(title:str):
    """
    search anidb id from title
    """
    global anidb_cache
    if not anidb_cache:
        get_anidb_id()
    result = process.extractOne(title, [x[3] for x in anidb_cache], score_cutoff=90)
    return anidb_cache[[x[3] for x in anidb_cache].index(result[0])][0] if result else None

async def get_info_from_anidb(id) -> str:
    """
    get anime info from anidb
    2 seconds only can request 1 time
    """
    async with aiohttp.ClientSession() as session:
        await asyncio.sleep(2)  # delay for 2 seconds
        async with session.get(f"http://api.anidb.net:9001/httpapi?request=anime&client={clientname}&clientver=1&protover=1&aid={id}") as r:
            if r.status != 200:
                return None
            text = await r.text()
            data = "https://cdn-eu.anidb.net/images/main/"+re.findall(r"<picture>(.*?)</picture>", text)[0]
            return data

def get_anidb_id():
    """
    one day only can request 1 time
    """
    if not os.path.exists("anime-titles.dat"):
        r = requests.get("http://anidb.net/api/anime-titles.dat.gz")
        with open("anime-titles.dat.gz", "wb") as f:
            f.write(r.content)
        with gzip.open('anime-titles.dat.gz', 'rb') as f_in:
            with open('anime-titles.dat', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    with open("anime-titles.dat", "r", encoding="utf-8") as f:
        data = []
        for line in f:
            if line.startswith("#"):
                continue
            # <aid>|<type>|<language>|<title>
            if line.split("|")[2] == "zh-Hans" or line.split("|")[2] == "zh-Hant":
                temp = line.split("|")
                temp[3] = temp[3].replace("\n", "").strip()
                data.append(temp)
    global anidb_cache
    anidb_cache = data

async def from_acggamer(keyword):
    """
    使用巴哈搜尋資料
    由於使用google服務， 需要proxy
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://cse.google.com/cse/element/v1?rsz=10&num=10&hl=zh-TW&source=gcsc&gss=.tw&cselibv=8435450f13508ca1&cx=partner-pub-9012069346306566%3Akd3hd85io9c&q={keyword}+more%3A%E6%89%BE%E4%BD%9C%E5%93%81&safe=active&cse_tok=AB-tC_6VMyQtkrLpd_OErEMPcBI-%3A1712904578463&sort=&exp=cc&callback=google.search.cse.api6738",
            headers=header
        ) as r:
            text = await r.text()
            if r.status != 200:
                return None
            if "Unauthorized access to internal API" in text:
                return None
            soup = BeautifulSoup(text, "html.parser")
            data = json.loads(soup.text.split("(")[1].split(")")[0])
            if data["results"]:
                for item in data["results"]:
                    print(item["titleNoFormatting"], unquote(item["url"]))

def get_anime1me_all() -> list[str]:
    r = requests.get("https://d1zquzjgwo9yb.cloudfront.net/").json()
    return [i[1] for i in r]

def tryprint(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("utf-8"))


"""
xxxanime: "xxx.png",

"""
async def main():
    for i in Allanime[:10]:
        id =  search_anidb_from_title(i)
        if id:
            data = await get_info_from_anidb(id)
        else:
            tryprint(f"{i} not found in anidb")
            data = await search_bangumi_from_title(i)
            if not data:
                tryprint(f"{i} not found in bangumi")
                data = await from_acggamer(i)
                if not data:
                    tryprint(f"{i} not found in acggamer")
                    data = await search_myanimelist_from_title(i,4)
                    if not data:
                        tryprint(f"{i} not found in myanimelist")
                        output[i] = None
                        continue
        output[i] = data
        tryprint(i+ " " + data)

if __name__ == "__main__":
    get_anidb_id()
    Allanime = get_anime1me_all()
    output = {}
    # ceeate a folder
    os.makedirs("dict", exist_ok=True)
    asyncio.run(main())
    with open(os.path.join("dict", "anime.json"), "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

