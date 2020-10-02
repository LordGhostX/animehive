import os
import requests
from bs4 import BeautifulSoup


def parse_anime_name(name):
    return ("]".join(name.split("]")[1:2]) + "]").strip()


def search_animepahe(title):
    params = {
        "m": "search",
        "l": 8,
        "q": title
    }
    r = requests.get("https://animepahe.com/api", params=params).json()
    return r.get("data", [])


def fetch_recommendations(anime_session, limit=5):
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
            "session": i.find("a")["href"].split("/")[-1],
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
        href = i.find("h3", {"class": "post-title"}).find("a")["href"]
        if href != "https://www.animeout.xyz/projects-list/":
            search_result.append({
                "title": i.find("h3", {"class": "post-title"}).text.strip(),
                "href": href,
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


def fetch_anime_info(session):
    r = requests.get("https://animepahe.com/anime/" + session)
    page = BeautifulSoup(r.text, "html.parser")
    try:
        poster = page.find("a", {"class": "youtube-preview"})["href"]
    except:
        poster = page.find("a", {"class": "poster-image"})["href"]
    return {
        "poster": poster,
        "synopsis": page.find("div", {"class": "anime-synopsis"}).text.strip(),
        "english": page.find("div", {"class": "anime-info"}).find_all("p")[0].text.strip(),
        "type": page.find("div", {"class": "anime-info"}).find_all("p")[1].text.strip(),
        "episodes": page.find("div", {"class": "anime-info"}).find_all("p")[2].text.strip(),
        "status": " ".join(page.find("div", {"class": "anime-info"}).find_all("p")[3].text.strip().split("\n")),
        "aired": " ".join(page.find("div", {"class": "anime-info"}).find_all("p")[4].text.strip().split("\n")),
        "season": " ".join(page.find("div", {"class": "anime-info"}).find_all("p")[5].text.strip().split("\n")),
        "genre": [i.text.strip() for i in page.find("div", {"class": "anime-genre"}).find_all("li")]
    }
