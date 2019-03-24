# MIT License

# Copyright (c) 2019 Jayanta Debnath

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
from db import DB

db = DB()

CSV = "X:\Google Drive\Documents\BackupCloud\LockerDatabase\database_20190323_slashed.csv"

fo = open(CSV)

while True:
    try:
        line = fo.readline()
        if not line:
            break
        arrFields = line.split(",")

        rel_path = arrFields[6]
        title = arrFields[5]
        rating = int(arrFields[1])
        playcount = int(arrFields[2])
        actor = arrFields[3]
        category = arrFields[4]

        lookup_path = None
        for movie in db.arrMovies:
            if os.path.basename(movie["rel_path"]) == title:
                lookup_path = movie["rel_path"]
                break

        if db.exists(lookup_path):
            if rating > 0:
                db.update(lookup_path, "rating", rating)
            if playcount > 0:
                db.update(lookup_path, "playcount", playcount)
            if not actor == "Unknown":
                db.update(lookup_path, "actor", actor)
            if not category == "Straight":
                db.update(lookup_path, "category", category)

    # ignore all errors
    except (UnicodeDecodeError, IndexError, ValueError) as e:
        continue
fo.close()