import sys
import os

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
    
main()