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

# imports
import os
import sys
import json
from datetime import datetime

# constants
CURDIR = os.path.dirname( sys.argv[0] )
DBDIR = os.path.join( CURDIR, "database.json" )

class DB:
    # contructor
    def __init__(self):
        self.arrData = []
        if not os.path.exists( DBDIR ):
            fo = open( DBDIR, "w" )
            fo.close()
        else:
            fo = open( DBDIR, "r" )
            contents = fo.read()
            if not len(contents) == 0:
                self.arrData = json.loads( contents )
            fo.close()
        
    def save(self):
        fo = open( DBDIR, "w" )
        fo.write( json.dumps( self.arrData, indent=4 ) )
        fo.close()
        
    def add(self, path):
        entry = {
            "title": os.path.basename(path),
            "timestamp": datetime.now().strftime("%Y-%m-%d_%H:%M:%S"),
            "isValid": True,
            "path": path,
            "rating": None,
            "playcount": 0,
            "actor": None,
            "category": "Straight",
            "delete": False,
            "split": False,
            "note": None
        }
        self.arrData.append( entry )
        self.save()