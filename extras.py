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


def fetch_recommendations(anime_session):
    r = requests.get("https://animepahe.com/anime/" + anime_session)
    page = BeautifulSoup(r.text, "html.parser")
    title = page.find("div", {"class": "title-wrapper"}
                      ).find("h1").text.strip()
    recommendation_section = page.find(
        "div", {"class": "anime-recommendation"})

    recommendations = []
    for i in recommendation_section.find_all("div", {"class": "mb-3"}):
        recommendations.append({
            "title": i.find("a")["title"],
            "type": i.find("strong").text.strip(),
            "season": i.find_all("a")[-1]["title"],
            "status": i.find("div", {"class": "col-9 px-1"}).text.strip().split("\n")[1]
        })
    return title, recommendations
