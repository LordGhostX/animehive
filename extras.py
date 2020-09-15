import requests
from bs4 import BeautifulSoup


def search_animepahe(title):
    params = {
        "m": "search",
        "l": 8,
        "q": title
    }
    r = requests.get("https://animepahe.com/api", params=params).json()
    return r.get("data", [])


def fetch_recommendations(anime_session, limit=8):
    r = requests.get("https://animepahe.com/anime/" + anime_session)
    page = BeautifulSoup(r.text, "html.parser")
    title = page.find("div", {"class": "title-wrapper"}
                      ).find("h1").text.strip()
    recommendation_section = page.find(
        "div", {"class": "anime-recommendation"})

    recommendations = []
    for i in recommendation_section.find_all("div", {"class": "mb-3"})[:limit]:
        recommendations.append({
            "title": i.find("a")["title"],
            "type": i.find("strong").text.strip(),
            "season": i.find_all("a")[-1]["title"],
            "status": i.find("div", {"class": "col-9 px-1"}).text.strip().split("\n")[1],
            "image": i.find("img")["src"]
        })
    return title, recommendations


def search_animeout(title):
    params = {"s": title}
    r = requests.get("https://www.animeout.xyz/", params=params)
    page = BeautifulSoup(r.text, "html.parser")

    search_result = []
    for i in page.find_all("div", {"class": "post-content"}):
        try:
            image = i.find("img")["src"]
        except:
            image = None
        search_result.append({
            "title": i.find("h3", {"class": "post-title"}).text.strip(),
            "href": i.find("h3", {"class": "post-title"}).find("a")["href"],
            "image": image
        })
    return search_result


def fetch_episodes(href):
    r = requests.get(href)
    page = BeautifulSoup(r.text, "html.parser")

    episodes = []
    for i in page.find_all("a"):
        try:
            if i["href"][-3:] == "mkv":
                episodes.append(i["href"])
        except:
            pass
    return episodes


def get_download_url(href):
    r = requests.get(href)
    pre_download_page = BeautifulSoup(r.text, "html.parser")
    pre_download_url = pre_download_page.find("a", {"class": "btn"})["href"]

    r = requests.get(pre_download_url)
    download_page = BeautifulSoup(r.text, "html.parser")
    download_url = download_page.find(
        "script", {"src": None}).contents[0].split('"')[1]
    return download_url
