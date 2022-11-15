import pandas as pd
import json
from datetime import datetime

from actordb import ACTORDB
actordb = ACTORDB()

arrMovies = []
fo = open('moviedb.json', 'r')
contents = fo.read()
if not len(contents) == 0:
    arrMovies = json.loads(contents)
    fo.close()

df = pd.DataFrame()
for movie in arrMovies:
    dftemp = pd.DataFrame({
        'timestamp': [movie['timestamp']],
        'rel_path': [movie['rel_path']],
        'rating': [movie['rating']],
        'playcount': [movie['playcount']],
        'actor': [movie['actor']],
        'category': [movie['category']],
        'actor_rating': [actordb.getRating(movie['actor'])]
    })
    df = pd.concat([df, dftemp], ignore_index=True)


df.to_excel('moviedb.xlsx')
