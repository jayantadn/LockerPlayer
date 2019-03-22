import sys
import os
from pathlib import Path

CURDIR = os.path.dirname( sys.argv[0] )
CONFIGFILE = os.path.join( CURDIR, "config.txt" )
CONFIG = dict()

def main():
    # check if config file exist, else exit
    if not os.path.exists( CONFIGFILE ):
        print( "ERROR: config file does not exist" )
        exit
        
    # open the config file and read all parameters
    fo = open( CONFIGFILE, "r" )
    while(True):
        line = fo.readline()
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
    
main()