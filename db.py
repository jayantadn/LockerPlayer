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


# strategy: what should be a unique identity of a movie
# title - possible duplicate filenames
# full path - the base movie folder may change.
# relative path - a movie may be moved from one folder to another.
# as of now relative path is selected, because moving a movie will change its stats anyway
# in future title is probably best, if we can find a way to preserve stats if a file is moved to different folder

class DB:
	"""database class"""
	# contructor
	def __init__(self):
		self.arrMovies = []
		if not os.path.exists(DBDIR):
			fo = open(DBDIR, "w")
			fo.close()
		else:
			fo = open(DBDIR, "r")
			contents = fo.read()
			if not len(contents) == 0:
				self.arrMovies = json.loads(contents)
			fo.close()

	def save(self):
		"""save database from to disk"""
		fo = open(DBDIR, "w")
		fo.write(json.dumps(self.arrMovies, indent=4))
		fo.close()

	def add(self, rel_path):
		"""add a new movie to database"""
		print("Adding to database: ", rel_path)
		entry = {
			"rel_path": rel_path,
			"timestamp": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
			"is_valid": True,
			"rating": None,
			"playcount": 0,
			"actor": rel_path.split("\\")[1],
			"category": "Straight",
			"delete": False,
			"split": False,
			"note": None
		}
		self.arrMovies.append(entry)
		self.save()

	def remove(self, rel_path):
		"""remove a movie from database"""

		# strategy: delete movie command from user will set the delete flag.
		# during fix_movie_folder(), the movie will be deleted from the actual filesystem.
		# then, the is_valid flag will be reset.
		# during refresh_db() the invalid flags will be removed from database

		for idx, data in enumerate(self.arrMovies):
			if data["rel_path"] == rel_path:
				print("Removing from database: ", rel_path)
				self.arrMovies[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
				self.arrMovies[idx]["is_valid"] = False
				self.save()
				break

	def update(self, rel_path, key, val):
		"""update attributes for a movie"""
		for idx, data in enumerate(self.arrMovies):
			if data["rel_path"] == rel_path:
				# its not very clear whether db library should do any validations
				# will wait and see what is better
				assert key in self.arrMovies[idx], "Invalid key"

				# formatting the value
				if key in ("rating", "playcount"):
					val = int(val)
				elif key in ("is_valid", "delete", "split"):
					if val is True or val == "True" :
						val = True
					else :
						val = False

				print("Updating ", key, "to ", val, "for ", rel_path)
				self.arrMovies[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
				self.arrMovies[idx][key] = val
				self.save()
				break

	def exists(self, rel_path):
		"""check if a movie exist in database"""
		flg_exist = False
		for data in self.arrMovies:
			if data["rel_path"] == rel_path:
				flg_exist = True
		return flg_exist

	def getIdxMovie(self, rel_path) :
		"""Get the idx of the given movie"""
		for idx, data in enumerate(self.arrMovies):
			if data["rel_path"] == rel_path:
				return idx

	def cleanup(self):
		"""remove the invalid entries"""
		for movie in self.arrMovies:
			if not movie["is_valid"]:
				print("Removing from database: ", movie["rel_path"])
				self.arrMovies.remove(movie)