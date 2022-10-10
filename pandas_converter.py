import pandas as pd
import json
from datetime import datetime

arrMovies = []
fo = open('moviedb.json', 'r')
contents = fo.read()
if not len(contents) == 0:
    arrMovies = json.loads(contents)
    fo.close()

header = {
    'timestamp': [datetime.now().strftime("%Y-%m-%d_%H:%M:%S")],
    'rel_path': ["header"],
    'rating': [0],
    'playcount': [0],
    'actor': ["header"],
    'category': ["header"]
}

df = pd.DataFrame(header)
for movie in arrMovies:
    dftemp = pd.DataFrame({
        'timestamp': [movie['timestamp']],
        'rel_path': [movie['rel_path']],
        'rating': [movie['rating']],
        'playcount': [movie['playcount']],
        'actor': [movie['actor']],
        'category': [movie['category']]
    })
    df = pd.concat([df, dftemp], ignore_index=True)

select = df['actor'] == "Kagney Linn Karter"
print(df[select])

df.to_excel('moviedb.xlsx')
df.to_json('moviedb_pandas.json')
