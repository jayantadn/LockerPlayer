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
        """Note: duplicate check is performed within this function"""
        
        if self.exists(actor) :
            print("Actor already exist: " + actor)
            return
        
        print("Adding actor to database:", actor)

        # create the entry
        entry = {
            "name": actor,
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            "rating": None
        }
        self.arrActors.append(entry)
        self.save()


    def remove(self, actor):
        """remove an actor from database"""

        print( "Removing from database: ", actor )
        self.arrActors.pop( self.getIdxActor(actor) )
        self.save()


    def rate(self, actor, val):
        """update rating for an actor"""
        
        for idx, data in enumerate(self.arrActors):
            if data["name"] == actor:
                print("Changing rating of", actor, "to", val)
                self.arrActors[idx]["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
                self.arrActors[idx]["rating"] = int(val)
                self.save()
                break


    def exists(self, actor):
        """check if an actor exist in database"""
        
        flg_exist = False
        for data in self.arrActors:
            if data["name"] == actor :
                flg_exist = True
        return flg_exist


    def getIdxActor(self, actor) :
        """Get the idx of the given actor"""
        
        for idx, data in enumerate(self.arrActors):
            if data["name"] == actor:
                return idx
