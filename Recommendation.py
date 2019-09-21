import time
from functools import lru_cache
import sys

from Rignak_MAL_Recommendations.plot import plot
from Rignak_Misc.TWRV import ThreadWithReturnValue as TWRV
from Rignak_Request.request import request_with_retry

"""
Use: 
>>> python Recommendation.py {username}
"""

WORLD_ORIGIN = "12549", "Dakara_Boku_wa_H_ga_Dekinai"
MAX_RECOMMENDATION_BY_ANIME = 5

@lru_cache(maxsize=2 ** 20)
def process_double_id(id1, id2):
    url = f"https://myanimelist.net/recommendations/anime/{id1}-{id2}"
    soup = request_with_retry(url)
    n = len(soup.find_all('div', {'class': 'spaceit_pad'}))
    return id1, id2, n


def process_anime(url):
    soup = request_with_retry(url)
    id1 = url.split('/')[-3]

    threads = []
    new_urls = []
    id2title = {}
    for div in soup.find_all('div', {'style': 'margin-bottom: 2px;'})[:MAX_RECOMMENDATION_BY_ANIME]:
        id2, title = div.find('a')['href'].split('/')[-2:]
        if int(id1) > int(id2):
            threads.append(TWRV(target=process_double_id, args=(id1, id2)))
        else:
            threads.append(TWRV(target=process_double_id, args=(id2, id1)))

        threads[-1].start()
        time.sleep(0.2)

        id2title[id2] = title
        new_urls.append(f"https://myanimelist.net/anime/{id2}/{title}/userrecs")

    recommendations = {(id1, id2): n for id1, id2, n in [thread.join(timeout=120) for thread in threads]}
    return recommendations, new_urls, id2title


def main(username):
    i, title = WORLD_ORIGIN

    id2title = {i: title}
    urls_to_request = [f'https://myanimelist.net/anime/{i}/{title}/userrecs']
    urls_seen = []
    recommendations = {}

    k = 0
    while len(urls_to_request) > 0:
        url = urls_to_request.pop(0)

        print(f"{k}|{len(urls_to_request)} | {url.split('/')[-2]}")
        try:
            new_recommendations, new_urls, new_id2title = process_anime(url)
            [urls_to_request.append(new_url) for new_url in new_urls if new_url not in urls_to_request + urls_seen]
            recommendations.update(new_recommendations)
            id2title.update(new_id2title)
        except Exception as e:
            print(e)

        if not k % 10:
            plot(recommendations, id2title, username)
        k += 1


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
