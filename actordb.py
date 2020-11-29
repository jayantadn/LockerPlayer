# MIT License

# Copyright (c) 2020 Jayanta Debnath

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


class ACTORDB:
	"""database class"""
	# contructor
	def __init__(self):
		self.arrActors = []
		if not os.path.exists(ACTORDBFILE):
			fo = open(ACTORDBFILE, "w")
			fo.close()
		else:
			fo = open(ACTORDBFILE, "r")
			contents = fo.read()
			if not len(contents) == 0:
				self.arrActors = json.loads(contents)
			fo.close()

	def save(self):
		"""save database from to disk"""
		fo = open(ACTORDBFILE, "w")
		fo.write(json.dumps(self.arrActors, indent=4))
		fo.close()

	def add(self, actor):
		"""add a new actor to database"""
        
        # this function will reject duplicate entries
                print("Actor already present in database: ", actor)
                return

		print("Adding actor to database:", actor)

		# create the entry
		entry = {
			"name": actor,
			"rating": None
		}
		self.arrActors.append(entry)
		self.save()
##### continue from here


	def remove(self, actor):
		"""remove an actor from database"""

        print( "Removing from database: ", actor )
        self.arrActors.pop( self.getIdxActor(actor) )
        self.save()

	def update(self, actor, key, val):
		"""update attributes for a movie"""
		for idx, data in enumerate(self.arrActors):
			if data["actor"] == actor:
				# its not very clear whether db library should do any validations
				# will wait and see what is better
				assert key in self.arrActors[idx], "Invalid key"

				# formatting the value
				if key in ("rating", "playcount"):
					val = int(val)

				print("Updating ", key, "to ", val, "for ", actor)
				self.arrActors[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
				self.arrActors[idx][key] = val
				self.save()
				break

	def exists(self, actor):
		"""check if a movie exist in database"""
		flg_exist = False
		for data in self.arrActors:
			if data["actor"] == actor:
				flg_exist = True
		return flg_exist

	def getIdxMovie(self, actor) :
		"""Get the idx of the given movie"""
		for idx, data in enumerate(self.arrActors):
			if data["actor"] == actor:
				return idx
