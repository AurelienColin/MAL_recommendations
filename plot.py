import subprocess
from graphviz import Digraph
import numpy as np
import os
import unicodedata

from Rignak_Misc.path import get_local_file
from Rignak_MAL_database.database import load

DOT_FILENAME = get_local_file(__file__, os.path.join('outputs', 'recommandations.dot'))
PNG_FILENAME = get_local_file(__file__, os.path.join('outputs', 'png', 'recommandations¤.png'))
THRESHOLD_FACTOR = 1
FONT_POWER = 2 / 3
EDGE_POWER = 1 / 3


def get_widths(id2title, recommendations):
    anime_widths = {}
    for anime_id in id2title:
        anime_widths[anime_id] = 0
        for (k1, k2), n in recommendations.items():
            if anime_id == k1 or anime_id == k2:
                anime_widths[anime_id] += recommendations[(k1, k2)]
    return anime_widths


def plot_nodes(graph, user_anime, id2title, anime_widths):
    threshold = np.mean(list(anime_widths.values())) * THRESHOLD_FACTOR

    for anime_id, title in id2title.items():
        if anime_id == 0 or anime_widths[anime_id] < threshold:
            continue
        color = ['red', 'green'][anime_id in user_anime]

        if len(title) > 20:
            title = title[:15] + '\n' + title[15:min(len(title), 30)]
        title = unicodedata.normalize('NFKD', title).encode('ascii', 'ignore').decode('ascii')

        graph.node(str(anime_id), title, _attributes={'fontsize': str(int(anime_widths[anime_id] ** FONT_POWER + 5)),
                                                      'penwidth': str(
                                                          max(1, int(anime_widths[anime_id] ** FONT_POWER) // 10)),
                                                      'color': color})


def plot_edges(graph, recommendations, anime_widths):
    threshold = np.mean(list(anime_widths.values())) * THRESHOLD_FACTOR

    for (id1, id2), n in recommendations.items():
        if id1 == 0 or anime_widths[id1] < threshold or anime_widths[id2] < threshold:
            continue
        graph.edge(str(id1), str(id2), _attributes={'penwidth': str(int(n ** EDGE_POWER)),
                                                    'dir': 'none'})


def plot(recommendations, id2title, username):
    user_anime = load(username)
    user_anime = [key for key, value in user_anime.items() if value['status'] == 2]

    graph = Digraph(comment='Anime Recommendations')

    anime_widths = get_widths(id2title, recommendations)
    plot_nodes(graph, user_anime, id2title, anime_widths)
    plot_edges(graph, recommendations, anime_widths)

    graph.render(DOT_FILENAME)
    subprocess.check_call(['sfdp', '-Tpng', DOT_FILENAME, '-o', PNG_FILENAME.replace('¤', str(len(anime_widths))),
                           '-Goverlap=prism ',
                           "-Gmodel=subset",
                           "-Gsplines=true"])
    os.remove(DOT_FILENAME + '.pdf')
