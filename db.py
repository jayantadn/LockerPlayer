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

# import external modules
import os
import sys
import json
from datetime import datetime

# import internal modules
from const import *


class DB:
    """database class"""
    # contructor
    def __init__(self):
        self.arrMovie = []
        if not os.path.exists(DBDIR):
            fo = open(DBDIR, "w")
            fo.close()
        else:
            fo = open(DBDIR, "r")
            contents = fo.read()
            if not len(contents) == 0:
                self.arrMovie = json.loads(contents)
            fo.close()

    def save(self):
        """save database from to disk"""
        fo = open(DBDIR, "w")
        fo.write(json.dumps(self.arrMovie, indent=4))
        fo.close()

    def add(self, rel_path):
        """add a new movie to database"""
        print("Adding to database: ", rel_path)
        entry = {
            "rel_path": rel_path,
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            "isValid": True,
            "rating": None,
            "playcount": 0,
            "actor": None,
            "category": "Straight",
            "split": False,
            "note": None
        }
        self.arrMovie.append(entry)
        self.save()

    def remove(self, rel_path):
        """remove a movie from database"""
        for idx, data in enumerate(self.arrMovie):
            if data["rel_path"] == rel_path:
                print("Removing from database: ", rel_path)
                self.arrMovie[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                self.arrMovie[idx]["isValid"] = False
                self.save()
                break

    def update(self, rel_path, key, val):
        """update attributes for a movie"""
        for idx, data in enumerate(self.arrMovie):
            if data["rel_path"] == rel_path:
                print("Updating ", key, "to ", val, "for ", rel_path)
                self.arrMovie[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                self.arrMovie[idx][key] = val
                self.save()
                break

    def exists(self, rel_path):
        """check if a movie exist in database"""
        flg_exist = False
        for data in self.arrMovie:
            if data["rel_path"] == rel_path:
                flg_exist = True
        return flg_exist
