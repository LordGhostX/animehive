import requests
from bs4 import BeautifulSoup


def search_animepahe(title):
    r = requests.get(
        f"https://animepahe.com/api?m=search&l=8&q={title}").json()
    return r.get("data", [])


def fetch_animepahe_recommendations(anime_session, limit=5):
    r = requests.get(f"https://animepahe.com/anime/{anime_session}")
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


def fetch_animepahe_info(session):
    r = requests.get(f"https://animepahe.com/anime/{session}")
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


def search_animeout(title):
    r = requests.get(f"https://www.animeout.xyz?s={title}")
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


def fetch_animeout_episodes(href):
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


def fetch_animeout_download(href):
    r = requests.get(href)
    pre_download_page = BeautifulSoup(r.text, "html.parser")
    pre_download_url = pre_download_page.find("a", {"class": "btn"})["href"]

    r = requests.get(pre_download_url)
    download_page = BeautifulSoup(r.text, "html.parser")
    download_url = download_page.find(
        "script", {"src": None}).contents[0].split('"')[1]
    return download_url


def search_gogoanime(title):
    r = requests.get(f"https://gogoanime.so//search.html?keyword={title}")
    page = BeautifulSoup(r.text, "html.parser")

    search_result = []
    for i in page.find("ul", {"class": "items"}).find_all("li"):
        try:
            search_result.append({
                "href": i.find("a")["href"],
                "title": i.find("p", {"class": "name"}).text.strip(),
                "released": i.find("p", {"class": "released"}).text.strip(),
                "image": i.find("img")["src"]
            })
        except:
            pass
    return search_result


def fetch_gogoanime_anime(href):
    r = requests.get(f"https://gogoanime.so{href}")
    page = BeautifulSoup(r.text, "html.parser")
    total_episodes = page.find("ul", {"id": "episode_page"}).find_all(
        "li")[-1].find("a")["ep_end"]
    alias = page.find("input", {"id": "alias_anime"})["value"]
    anime_id = page.find("input", {"id": "movie_id"})["value"]

    return int(total_episodes), alias, anime_id


def fetch_gogoanime_episodes(start, end, alias, anime_id):
    r = requests.get(
        f"https://ajax.gogocdn.net/ajax/load-list-episode?ep_start={start}&ep_end={end}&id={anime_id}&default_ep=0&alias={alias}")
    page = BeautifulSoup(r.text, "html.parser")

    episodes = []
    for i in page.find_all("li"):
        try:
            episodes.append({
                "href": i.find("a")["href"].strip(),
                "name": i.find("div", {"class": "name"}).text.strip()
            })
        except:
            pass
    return episodes[::-1]


def fetch_gogoanime_download(href):
    r = requests.get(f"https://gogoanime.so{href}")
    pre_download_page = BeautifulSoup(r.text, "html.parser")
    anime_title = pre_download_page.find(
        "div", {"class": "title_name"}).text.strip()
    pre_download_url = pre_download_page.find(
        "li", {"class": "dowloads"}).find("a")["href"]

    r = requests.get(pre_download_url)
    download_page = BeautifulSoup(r.text, "html.parser")
    download_links = []

    for i in download_page.find_all("div", {"class": "dowload"}):
        try:
            download_links.append({
                "name": " ".join([i.strip() for i in i.text.split("\n")]),
                "href": i.find("a")["href"]
            })
        except:
            pass
    return anime_title, download_links


def fetch_gogoanime_latest(limit=10):
    r = requests.get("https://gogoanime.so/")
    page = BeautifulSoup(r.text, "html.parser")

    latest_items = []
    for item in page.find("div", {"class": "last_episodes"}).find_all("li")[:limit]:
        try:
            latest_items.append({
                "href": item.find("a")["href"],
                "name": item.find("p").text.strip(),
                "episode": item.find("p", {"class": "episode"}).text.strip(),
                "image": item.find("img")["src"]
            })
        except:
            pass
    return latest_items
