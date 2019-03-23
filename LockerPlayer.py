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
import sys  
import os   
import shutil
import time
import random
import json
from consolemenu import *
from consolemenu.items import *

# import internal modules
from db import DB

# constants
CURDIR = os.path.dirname( sys.argv[0] )
TMPDIR = os.path.join( CURDIR, "tmp" )
CONFIGFILE = os.path.join( CURDIR, "config.txt" )
CONFIG = dict()

# global variables
arrDB = []
      
db = DB()

# all function definitions

def cleanup():
    shutil.rmtree( TMPDIR )
        
def getConfig():
    # check if config file exist, else exit
    if not os.path.exists( CONFIGFILE ):
        print( "[ERROR] config file does not exist" )
        quit()
        
    # open the config file and read all parameters
    fo = open( CONFIGFILE, "r" )
    while(True):
        line = fo.readline() # this will include the newline character which needs to be removed later
        if not line: break
        key = line.split("=")[0]
        val = line.split("=")[1]
        CONFIG[key] = val
    fo.close()

    # check if all the configuration exist
    if not "MOVIEDIR" in CONFIG or not "PLAYER" in CONFIG or not "SPLITTER" in CONFIG:
        print( "[ERROR] Invalid configuration" )
        quit()        

    # strip the newline character from each parameter
    for key in CONFIG:
        CONFIG[key] = CONFIG[key][:-1]

    # validate the configuration
    if not os.path.isdir( os.path.normpath(CONFIG["MOVIEDIR"]) ):
        print( "[ERROR] Configured movie directory does not exist" )
        quit()
    if not os.path.isfile(CONFIG["PLAYER"]):
        print( "[ERROR] Configured movie player does not exist" )
        quit()
    if not os.path.isfile(CONFIG["SPLITTER"]):
        print( "[WARNING] Configured movie splitter does not exist" )

    # create tmp folder
    if os.path.exists( TMPDIR ): 
        shutil.rmtree( TMPDIR )
    while( os.path.exists( TMPDIR ) ): 
        time.sleep( 0.01 )
    os.mkdir( TMPDIR )

   
def playFile():
    id = random.randrange( 0, len(arrDB), 1 )
    os.system( CONFIG["PLAYER"] + " " + arrDB[id]["path"] )
   
def refreshDB():
    arrFilenameErrors = []
    arrDirnameErrors = []
    for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
        for file in files:
            # check if filename is valid
            try:
                print( "Adding to database: ", os.path.join(root, file) )
            except UnicodeEncodeError:
                arrFilenameErrors.append( root )
            
            # adding file to database
            entry = {
                "title": file,
                "path": os.path.join(  root, file )
            }
            arrDB.append( entry )
            
    # display the filename and dirname errors
    if not len(arrFilenameErrors) == 0:
        print( "[WARNING] Invalid file or folder name found under:" )
        for pardir in arrFilenameErrors:
            try:
                print( pardir )
            except UnicodeEncodeError:
                arrDirnameErrors.append( pardir )
        for pardir in arrDirnameErrors:
            try:
                print( os.path.dirname(pardir) )
            except UnicodeEncodeError:
                print( "[WARNING] Invalid names found in some unidentified folders" )
        fix = input( "Please fix the filenames manually. [F]ixed, [S]kip " )
        if fix in ('F', 'f'):
            print( "Filenames are assumed fixed. Refreshing database again" )
            refreshDB()
            
    # dump to json file
    fo = open( "database.json", "w" )
    fo.write( json.dumps( arrDB, indent=4 ) )
    fo.close()
    
def showmenuMain():
    menuMain = ConsoleMenu("Main menu")
    itemPlayFile = FunctionItem("Play a random file", playFile)
    menuMain.append_item( itemPlayFile )
    
    menuOther = ConsoleMenu("Other options")
    itemRefreshDB = FunctionItem("Refresh database", refreshDB)
    menuOther.append_item( itemRefreshDB )
    
    itemOther = SubmenuItem("Other options", menuOther, menuMain)
    menuMain.append_item( itemOther )
    menuMain.show()


def main():
    #getConfig()
    #showmenuMain()
    #cleanup()
    db.remove( "X:\.Locker\Videobox\Brittney Skye\Snow Job part3.mkv" )
    #print( db.arrData )
    
# invoke the main
main()
