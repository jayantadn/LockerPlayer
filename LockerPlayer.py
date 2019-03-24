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
from const import *
from db import DB

# global variables
CONFIG = dict()
db = DB()


# --- all function definitions ---

def cleanup():
    """remove all deleted files from database."""
    shutil.rmtree(TMPDIR)


def get_config():
    """read the configuration file and retrieve the configuration parameters"""

    # check if config file exist, else exit
    if not os.path.exists(CONFIGFILE):
        print("[ERROR] config file does not exist")
        quit()

    # open the config file and read all parameters
    fo = open(CONFIGFILE, "r")
    while True:
        line = fo.readline()  # this will include the newline character which needs to be removed later
        if not line: break
        key = line.split("=")[0]
        val = line.split("=")[1]
        CONFIG[key] = val
    fo.close()

    # check if all the configuration exist
    if "MOVIEDIR" not in CONFIG or "PLAYER" not in CONFIG or "SPLITTER" not in CONFIG:
        print("[ERROR] Invalid configuration")
        quit()

    # strip the newline character from each parameter
    for key in CONFIG:
        CONFIG[key] = CONFIG[key][:-1]

    # validate the configuration
    if not os.path.isdir(os.path.normpath(CONFIG["MOVIEDIR"])):
        print("[ERROR] Configured movie directory does not exist")
        quit()
    if not os.path.isfile(CONFIG["PLAYER"]):
        print("[ERROR] Configured movie player does not exist")
        quit()
    if not os.path.isfile(CONFIG["SPLITTER"]):
        print("[WARNING] Configured movie splitter does not exist")

    # create tmp folder
    if os.path.exists(TMPDIR):
        shutil.rmtree(TMPDIR)
    while os.path.exists(TMPDIR):
        time.sleep(0.01)
    os.mkdir(TMPDIR)


def play_file():
    """play a given file. if no parameters provided, play random."""
    if not len(db.arrData) == 0:
        idx = random.randrange(0, len(db.arrData), 1)
        os.system(CONFIG["PLAYER"] + " " + db.arrData[idx]["path"])
    else:
        input("[ERROR] No movies found. Press <enter> to continue...")


def refresh_db():
    """traverse movie folder and update the database"""
    arr_filename_errors = []
    arr_dirname_errors = []
    for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
        for file in files:
            # creating the full path
            path = os.path.join(root, file)

            # check if filename is valid
            try:
                print("Adding to database: ", path)
            except UnicodeEncodeError:
                arr_filename_errors.append(root)

            # adding file to database
            if not db.exists(path):
                db.add(path)

    # display the filename and dirname errors
    if not len(arr_filename_errors) == 0:
        print("[WARNING] Invalid file or folder name found under:")
        for pardir in arr_filename_errors:
            try:
                print(pardir)
            except UnicodeEncodeError:
                arr_dirname_errors.append(pardir)
        for pardir in arr_dirname_errors:
            try:
                print(os.path.dirname(pardir))
            except UnicodeEncodeError:
                print("[WARNING] Invalid names found in some unidentified folders")
        fix = input("Please fix the filenames manually. [F]ixed, [S]kip ")
        if fix in ('F', 'f'):
            print("Filenames are assumed fixed. Refreshing database again")
            refresh_db()


def show_menu_main():
    """show the main menu"""
    menu_main = ConsoleMenu("Main menu")
    item_play_file = FunctionItem("Play a random file", play_file)
    menu_main.append_item(item_play_file)

    menu_other = ConsoleMenu("Other options")
    item_refresh_db = FunctionItem("Refresh database", refresh_db)
    menu_other.append_item(item_refresh_db)

    item_other = SubmenuItem("Other options", menu_other, menu_main)
    menu_main.append_item(item_other)
    menu_main.show()


def main():
    """program entry point"""
    get_config()
    show_menu_main()
    cleanup()


# invoke the main
main()
