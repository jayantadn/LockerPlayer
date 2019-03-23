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

def cleanup():
    shutil.rmtree( TMPDIR )
        
def getConfig():
    # check if config file exist, else exit
    if not os.path.exists( CONFIGFILE ):
        print( "ERROR: config file does not exist" )
        exit
        
    # open the config file and read all parameters
    fo = open( CONFIGFILE, "r" )
    while(True):
        line = fo.readline() # this will include the newline character which needs to be removed later
        if not line: break
        key = line.split("=")[0]
        val = line.split("=")[1]
        CONFIG[key] = val
    fo.close()

    # validate the configuration
    if not os.path.isdir( os.path.normpath(CONFIG["MOVIEDIR"][:-1]) ):
        print( "ERROR: Configured movie directory does not exist" )
        exit
    if not os.path.isfile(CONFIG["PLAYER"][:-1]):
        print( "ERROR: Configured movie player does not exist" )
        exit
    if not os.path.isfile(CONFIG["SPLITTER"][:-1]):
        print( "WARNING: Configured movie splitter does not exist" )

    # create tmp folder
    if os.path.exists( TMPDIR ): shutil.rmtree( TMPDIR )
    while( os.path.exists( TMPDIR ) ): time.sleep( 0.01 )
    os.mkdir( TMPDIR )

def main():
    getConfig()
    showmenuMain()
    cleanup()
   
def playFile():
    print( "Play some file" )
   
def refreshDB():
    print( "refresh DB" )
    
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
    
# invoke the main
main()
