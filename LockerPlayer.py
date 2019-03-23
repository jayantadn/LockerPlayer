# imports
import sys  # for arguments
import os   # for path resolving and manipulation
import shutil # rmtree
import time
from consolemenu import *
from consolemenu.items import *

# constants
CURDIR = os.path.dirname( sys.argv[0] )
TMPDIR = os.path.join( CURDIR, "tmp" )
CONFIGFILE = os.path.join( CURDIR, "config.txt" )
CONFIG = dict()

# global variables
arrDB = []

def cleanup():
    shutil.rmtree( TMPDIR )
        
def getConfig():
    print( "Reading configuration file and doing initial setup" )
    
    # check if config file exist, else exit
    if not os.path.exists( CONFIGFILE ):
        print( "ERROR: config file does not exist" )
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
        print( "ERROR: Invalid configuration" )
        quit()        

    # strip the newline character from each parameter
    for key in CONFIG:
        CONFIG[key] = CONFIG[key][:-1]

    # validate the configuration
    if not os.path.isdir( os.path.normpath(CONFIG["MOVIEDIR"]) ):
        print( "ERROR: Configured movie directory does not exist" )
        quit()
    if not os.path.isfile(CONFIG["PLAYER"]):
        print( "ERROR: Configured movie player does not exist" )
        quit()
    if not os.path.isfile(CONFIG["SPLITTER"]):
        print( "WARNING: Configured movie splitter does not exist" )

    # create tmp folder
    if os.path.exists( TMPDIR ): 
        shutil.rmtree( TMPDIR )
    while( os.path.exists( TMPDIR ) ): 
        time.sleep( 0.01 )
    os.mkdir( TMPDIR )

   
def playFile():
    print( "Play some file" )
   
def refreshDB():
    print( "Reading movie directory and refreshing database" )
    
    for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
        for file in files:
            entry = {
                "title": file,
                "path": os.path.join(  root, file )
            }
            arrDB.append( entry )

    print( arrDB[1] )
    
def showmenuMain():
    menuMain = ConsoleMenu("Main menu")
    itemPlayFile = FunctionItem("Play a random file", playFile)
    menuMain.append_item( itemPlayFile )
    
    menuOther = ConsoleMenu("Main menu cntd...")
    itemRefreshDB = FunctionItem("Refresh database", refreshDB)
    menuOther.append_item( itemRefreshDB )
    
    itemOther = SubmenuItem("Other options", menuOther, menuMain)
    menuMain.append_item( itemOther )
    menuMain.show()


def main():
    getConfig()
    showmenuMain()
    cleanup()
    
# invoke the main
main()
