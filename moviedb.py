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

class MOVIEDB:
	"""database class"""
	# contructor
	def __init__(self):
		self.arrMovies = []
		if not os.path.exists(MOVIEDBFILE):
			fo = open(MOVIEDBFILE, "w")
			fo.close()
		else:
			fo = open(MOVIEDBFILE, "r")
			contents = fo.read()
			if not len(contents) == 0:
				self.arrMovies = json.loads(contents)
			fo.close()

	def save(self):
		"""save database from to disk"""
		fo = open(MOVIEDBFILE, "w")
		fo.write(json.dumps(self.arrMovies, indent=4))
		fo.close()

	def add(self, rel_path):
		"""add a new movie to database"""

		print("Adding to database:", rel_path)

		# finding the actor name. Its basically the second folder from rel_path
		folder1 = None
		folder2 = None
		head = rel_path
		while True:
			head, tail = os.path.split(head)
			folder2 = folder1
			folder1 = tail
			if len(head) == 0 : break
		actor = folder2

		# create the entry
		entry = {
			"rel_path": rel_path,
			"timestamp": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
			"rating": None,
			"playcount": 0,
			"actor": actor,
			"category": "Straight",
		}
		self.arrMovies.append(entry)
		self.save()

	def remove(self, rel_path):
		"""remove a movie from database"""

		# strategy: old strategy was to set a flag when a movie is deleted.
		# later during cleanup, those files will be actually deleted.
		# But its observed that the flag is often forgotten in different functions.
		# So, decision is taken to delete the file directly.
		# Also, remove the entry from database
		# If new requirements come in future, we will think about then.

		# delete the file from database
		print( "Removing from database:", rel_path )
		self.arrMovies.pop( self.getIdxMovie(rel_path) )
		self.save()

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
