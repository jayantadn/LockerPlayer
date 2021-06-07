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

# A custom assert implementation
def myassert(expr, msg) :
    if not expr :
        print("ERROR: " + msg)
        input("Press enter to exit...")
        exit(1)
        
        
# import external modules
try :
    import sys
    import os
    import shutil
    import time
    import random
    import traceback
    from send2trash import send2trash
    import getpass
    import subprocess
    import progressbar # pip install progressbar2
    import hashlib
except :
    myassert(False, "Import failed")
    
# import internal modules
from const import *
from moviedb import MOVIEDB
from actordb import ACTORDB
from Menu import *

# global variables
CONFIG = dict()
moviedb = MOVIEDB()
actordb = ACTORDB()


# --- all function definitions ---

def copy_hi_movies():
    """Copy high rated movies to another location"""

    # user inputs
    destdir = input( "Enter destination: " )
    rating = input( "Enter the minimum rating: ")
    if not os.path.isdir(destdir) :
        os.makedirs( destdir )

    # loop through the database and create list of movies with high rating
    filelist = []
    for movie in moviedb.arrMovies:
        if movie["rating"] is not None and movie["rating"] >= int(rating):
            src = os.path.join(CONFIG["MOVIEDIR"], movie["rel_path"])
            dest = os.path.join(destdir, movie["rel_path"])
            if not os.path.exists(dest):
                filelist.append( [src, dest] )

    # select xcopy if exists
    copy = None
    try :
        subprocess.check_output(["where", "xcopy"])
        copy = "xcopy"
    except :
        pass
        
    # perform copy
    for fileset in progressbar.progressbar(filelist) :
        if not os.path.exists( os.path.dirname( fileset[1] ) ) :
            os.makedirs( os.path.dirname( fileset[1] ) )
        if copy == "xcopy" :
            subprocess.run( [ "xcopy", fileset[0], os.path.dirname(fileset[1]), "/j/q" ], stdout=subprocess.DEVNULL )
        else :
            shutil.copy2( fileset[0], fileset[1] )
            
            
def delete_movie(rel_path) :
    print("deleting file: ", rel_path)
    send2trash(os.path.join(CONFIG["MOVIEDIR"], rel_path))
    if moviedb.exists(rel_path):
        moviedb.remove(rel_path)


def fix_actor_db():
    """fix anything wrong with the json database of actors"""
    
    # remove actor if no movies found
    for actor in actordb.arrActors :
        found = False
        for movie in moviedb.arrMovies :
            if actor["name"] == movie["actor"] :
                found = True
                break
        if not found :
            print("Removing actor as no movies found:", actor["name"])
            actordb.remove(actor["name"])


def fix_movie_folder():
    """fix problems in the movie folder"""

    # strategy: fix movie folder should only fix problems in the movie folder.
    # It should not touch the database.

    # local variables
    arr_filename_errors = []
    arr_dirname_errors = []

    # algorithm: try to print full path of all files. If some invalid
    # characters are found in the filename, exception will be thrown.
    # List the parent folder of such files. If parent folder name also has
    # invalid characters, print the parent of parent.
    # assumption: only movie name or movie folder names can have errors.
    # Any other parent folder is very likely manually created.

    # traverse through movie folder and check if all filenames are valid
    arrDelete = []
    arrCase = []
    arrEmptyFolders = []
    for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]) :
        if len(subdirs) + len(files) == 0 :
            arrEmptyFolders.append(root)
    
        for file in files:
            path = os.path.join(root, file)
            try:
                # extract the relative path
                rel_path = path[len(CONFIG["MOVIEDIR"])::][1:]

                # mark non movie files for delete
                ext = os.path.splitext(path)[1]
                if ext not in EXTLIST:
                    arrDelete.append(rel_path)

                # convert actor name to title case
                folder1 = None
                folder2 = None
                head = path
                while True :
                    head, tail = os.path.split(head)
                    folder2 = folder1
                    folder1 = tail
                    if head == CONFIG["MOVIEDIR"] : break
                actor = folder2
                if actor != actor.title() :
                    partpath = path[: path.find(actor) + len(actor) ]
                    if partpath not in arrCase :
                        arrCase.append(partpath)

            except UnicodeEncodeError:
                arr_filename_errors.append(root)

    # delete all empty folders
    if len(arrEmptyFolders) > 0 :
        for folder in arrEmptyFolders :
            print(folder)
        confirm = input("\nThe above folders are empty and will be removed. Please confirm (y/n): ")
        if confirm == "y" :
            for folder in arrEmptyFolders :
                os.rmdir(folder)

    # display the filename and dirname errors
    if len(arr_filename_errors) > 0 :
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

    # delete the non movie files
    elif len(arrDelete) > 0 :
        for rel_path in arrDelete :
            delete_movie(rel_path)

    # change actor names to title case
    elif len(arrCase) > 0 :
        print( "The following path need to be changed to title case:")
        for partpath in arrCase : print(partpath)
        cont = input( "Do you want to continue?\n 1. Yes\t 2. No ")
        if cont == "1" :
            # renaming first with _ suffix as windows does not allow
            # case change in filename
            for partpath in arrCase:
                src = partpath
                head, tail = os.path.split(partpath)
                dest = os.path.join( head, tail.title() )

                os.rename( src, dest + "_" )
                time.sleep(1)
            for partpath in arrCase:
                head, tail = os.path.split(partpath)
                src = os.path.join( head, tail.title() + "_" )
                os.rename( src, src[:-1] )

    else :
        print( "\nNo errors found" )


def init():
    """read the configuration file and retrieve the configuration parameters"""

    # run the script only with a password
    while True:
        passwd = getpass.getpass()
        h = hashlib.md5()
        h.update(passwd.encode("utf-8"))
        if not h.hexdigest() == "76a2173be6393254e72ffa4d6df1030a" :
            print("Invalid password. Try again.")
        else:
            break

    # check if config file exist, else exit
    if not os.path.exists(CONFIGFILE):
        print("[ERROR] config file does not exist")
        quit()

    # open the config file and read all parameters
    fo = open(CONFIGFILE)
    while True:
        line = fo.readline()  # this will include the newline character which needs to be removed later
        if not line:
            break
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
    if not os.path.isdir(CONFIG["MOVIEDIR"]):
        print("[ERROR] Configured movie directory does not exist")
        quit()
    if not os.path.isfile(CONFIG["PLAYER"]):
        print("[ERROR] Configured movie player does not exist")
        quit()
    if not os.path.isfile(CONFIG["SPLITTER"]):
        print("[WARNING] Configured movie splitter does not exist")


def play_actor(actor=None) :
    """Play movies for a given actor. If no actor specified, prompt for one."""

    # if no actor is specified, prompt for the actor name.
    # partial match is ok. list all actors matching the name.
    if actor is None :
        actor = input( "Actor name: " )
        arrActor = []
        for movie in moviedb.arrMovies:
            if actor in movie["actor"] and movie["actor"] not in arrActor:
                arrActor.append( movie["actor"] )

        # If no match, throw error
        # if single match, then trouble free
        # if multiple match, then prompt to select one
        assert len(arrActor) != 0, "No such actor found"
        if len(arrActor) == 1 :
            actor = arrActor[0]
        else :
            for i, actor in enumerate(arrActor) :
                print( i, actor)
            print( i+1, "Go back" )
            i = int( input( "Please select an actor: " ) )
            assert 0 <= i <= len(arrActor), "Invalid input"
            if i == len(arrActor) : return # Go back
            actor = arrActor[i]

    # create array of movies by actor. give movie array to randomize
    arrMovies = []
    for movie in moviedb.arrMovies:
        if actor == movie["actor"] :
            arrMovies.append(movie)
    if len(arrMovies) == 0 :
        print("No movies found for actor:", actor)
        return
    play_random(arrMovies)


def play_rated() :
    """Play a high rated movie"""
    rating = int( input("Enter the minimum rating: ") )
    arrMovies = []
    for movie in moviedb.arrMovies :
        if movie["rating"] is not None and movie["rating"] >= rating :
            arrMovies.append(movie)
    play_random(arrMovies)


def play_unrated() :
    """Play an unrated movie"""
    arrMovies = []
    for movie in moviedb.arrMovies :
        if movie["rating"] is None :
            arrMovies.append(movie)
    play_random(arrMovies)


def play_unrated_actor() :
    """Play an unrated actor"""
            
    actorlist = []
    for actor in actordb.arrActors :
        if actor["rating"] is None :
            actorlist.append(actor)
            
    play_random_actor(actorlist)

def play_unplayed_actor() :
    """Play an actor never played before"""

    actorlist = []
    for actor in actordb.arrActors :
        cnt_movies = 0
        for movie in moviedb.arrMovies :
            if movie["actor"] == actor["name"] :
                if movie["playcount"] > 0 :
                    break
            cnt_movies += 1
        if cnt_movies >= len(moviedb.arrMovies) :
            actorlist.append(actor)

    play_random_actor(actorlist)


def play_file(rel_path):
    """play the movie and update stats"""

    assert os.path.exists( os.path.join(CONFIG["MOVIEDIR"], rel_path) ), "File not found"

    idxMovie = moviedb.getIdxMovie(rel_path)

    playcount = int(moviedb.arrMovies[idxMovie]["playcount"]) + 1
    moviedb.update(moviedb.arrMovies[idxMovie]["rel_path"], "playcount", playcount)

    os.system(CONFIG["PLAYER"] + " " + os.path.join(CONFIG["MOVIEDIR"],
        moviedb.arrMovies[idxMovie]["rel_path"]))

    show_menu_postplay(rel_path)

def play_random(arrMovies = moviedb.arrMovies) :
    assert len(arrMovies) > 0, \
        "[ERROR] No movies found"

    while True:
        # get a random file
        idx = random.randrange(0, len(arrMovies), 1)

        # print stats for the file
        print("")
        print("We found the following movie for you:")
        print("title = ", os.path.basename(arrMovies[idx]["rel_path"]))
        print("category = ", arrMovies[idx]["category"])
        print("rating = ", arrMovies[idx]["rating"])

        choice = input( "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_file(arrMovies[idx]["rel_path"])

        elif choice == "2":
            continue

        elif choice == "0" :
            show_menu_main()
            break

        else :
            print( "ERROR: Invalid choice" )
            break


def play_random_actor(actorlist=actordb.arrActors):
    """Play a random actor from ActorDB"""
    
    while True:
        idx = random.randrange(0, len(actorlist), 1)
        actor = actorlist[idx]["name"]
        if actor is not None and not actor == "Unknown":
            show_stats_actor(actor)
        
        choice = input( "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_actor(actor)

        elif choice == "2":
            continue

        elif choice == "0" :
            show_menu_main()
            break

        else :
            print( "ERROR: Invalid choice" )
            break       


def play_rated_actor():
    """Play movie for a high rated actor"""
    
    # fetch minimum rating from user
    rating = int( input("Please enter minimum rating for actor: ") )
    
    # create a list of actors with at least given rating
    actorlist = []
    for actor in actordb.arrActors :
        if actor["rating"] is not None :
            if int( actor["rating"] ) >= rating :
                actorlist.append(actor["name"])

    # randomize and play actor from the list
    while True:
        idx = random.randint(0, len(actorlist)-1)
        actor = actorlist[idx]
        if actor is not None and not actor == "Unknown":
            show_stats_actor(actor)
        
        choice = input( "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_actor(actor)

        elif choice == "2":
            continue

        elif choice == "0" :
            show_menu_main()
            break

        else :
            print( "ERROR: Invalid choice" )
            break       


def refresh_db():
    """traverse movie folder and update the database"""

    fix_movie_folder()
    fix_actor_db()

    # change actor names to title case
    for movie in moviedb.arrMovies :
        if movie["actor"] != movie["actor"].title() :
            rel_path_new = movie["rel_path"].replace( movie["actor"],
                movie["actor"].title(), 1 )
            if os.path.exists( os.path.join(CONFIG["MOVIEDIR"], rel_path_new) ) :
                moviedb.update(movie["rel_path"], "rel_path", rel_path_new)
                moviedb.update(movie["rel_path"], "actor", movie["actor"].title())

    # check for non-existent entries in database
    arrDelete = []
    for movie in moviedb.arrMovies:
        full_path = os.path.join(CONFIG["MOVIEDIR"], movie["rel_path"])
        if not os.path.exists(full_path):
            arrDelete.append(movie["rel_path"])
    if len(arrDelete) > 0 :
        print( "The following files will be removed from database.")
        print( "Please verify whether they actually exist in the filesystem")
        for rel_path in arrDelete :
            print(rel_path)
        delete = input("Are you sure to delete them?\n 1. Yes\t 2. No ")
        if delete == "1" :
            for rel_path in arrDelete :
                delete_movie(rel_path)

    # add any new files
    for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
        for file in files:
            # add to database if not exist already
            # assuming non-movie files are already deleted
            path = os.path.join(root, file)
            rel_path = path[len(CONFIG["MOVIEDIR"])::][1:]
            if not moviedb.exists(rel_path):
                moviedb.add(rel_path)

    print( "\nDatabase refresh completed." )


def show_menu_main():
    """show the main menu"""

    menu = Menu()
    menu.add( MenuItem( "Play by movie", show_menu_movie ) )
    menu.add( MenuItem( "Play by actor", show_menu_actor ) )
    menu.add( MenuItem( "Other options", show_menu_other ) )
    while True : menu.show()
    
    

def show_menu_other():
    """show menu which could not fit into main menu"""

    menu = Menu(show_menu_main)
    menu.add( MenuItem( "Refresh database", refresh_db ) )
    menu.add( MenuItem( "Show overall statistics", show_stats_overall ) )
    menu.add( MenuItem( "Copy high rated movies", copy_hi_movies ) )
    while True : menu.show()
    

def show_menu_movie():
    """show menu to select a movie"""

    menu = Menu()
    menu.add( MenuItem( "Play a random movie", play_random ) )
    menu.add( MenuItem( "Play a hi rated movie", play_rated ) )
    menu.add( MenuItem( "Play an unrated movie", play_unrated ) )
    while True : menu.show()

def show_menu_actor():
    """show menu to select an actor"""

    menu = Menu()
    menu.add( MenuItem( "Play selected actor", play_actor ) )
    menu.add( MenuItem( "Play random actor", play_random_actor ) )
    menu.add( MenuItem( "Play a high rated actor", play_rated_actor ) )
    menu.add( MenuItem( "Play an unrated actor", play_unrated_actor ) )
    menu.add( MenuItem( "Play an actor never played before", play_unplayed_actor ) )
    while True : menu.show()


# post play menu
def show_menu_postplay(rel_path):
    idxMovie = moviedb.getIdxMovie(rel_path)

    menu = Menu(show_menu_main)
    
    menu.add( MenuItem( "Repeat actor", lambda : play_actor(moviedb.arrMovies[idxMovie]["actor"]) ) ) 

    def irate_movie() :
        rating = input("Enter your rating: ")
        moviedb.update(moviedb.arrMovies[idxMovie]["rel_path"], "rating", rating)
    menu.add( MenuItem( "Rate movie", irate_movie) )
    
    def irate_actor() :
        actor = moviedb.arrMovies[idxMovie]["actor"]
        rating = input("Please enter rating for actor " + actor + " : ")
        actordb.rate(actor, rating)
    menu.add( MenuItem( "Rate actor", irate_actor) )

    def idelete_movie() :
        delete = input("Are you sure to delete this movie?\n 1. Yes\t 2. No ")
        if delete == "1":
            delete_movie(rel_path)
        show_menu_main() # movie index has changed, other menu items here wont work as expected
    menu.add( MenuItem( "Delete movie", idelete_movie) )

    def idelete_actor() :
        actor = moviedb.arrMovies[idxMovie]["actor"]
        print("Are you sure to delete all movies of", actor, "?")
        delete = input("1. Yes\t 2. No ")
        if delete == "1":
            arrDelete = []
            for movie in moviedb.arrMovies:
                if movie["actor"] == actor:
                    arrDelete.append(movie["rel_path"])
            for rel_path in arrDelete:
                delete_movie(rel_path)
        show_menu_main() # movie index has changed, other menu items here wont work as expected
    menu.add( MenuItem( "Delete actor", idelete_actor) )
    
    def iupdate_stats() :
        entry = 1
        for key, val in moviedb.arrMovies[idxMovie].items():
            if key != "rel_path" and key != "timestamp":
                print(entry, key.ljust(10), val)
                entry += 1
        print(0, "Go back..")
        choice = int( input("Which field do you want to update: ") )
        entry = 1
        for key, val in moviedb.arrMovies[idxMovie].items():
            if key != "rel_path" and key != "timestamp":
                if entry == choice :
                    val = input("Please enter new value for " + key + " : ")
                    moviedb.update(rel_path, key, val)
                    break
                entry += 1
    menu.add( MenuItem( "Update stats", iupdate_stats) )
    
    while True : menu.show()


def show_stats_actor(actorname):
    """Show the statistics for an actor"""

    # calculate number of movies
    arrMovies = moviedb.arrMovies
    cnt_rated = 0
    cnt_played = 0
    cnt_movies = 0
    for movie in arrMovies:
        if movie["actor"] == actorname:
            if movie["playcount"] != 0:
                cnt_played += 1
            if movie["rating"] is not None:
                cnt_rated += 1
            cnt_movies += 1
            
    # print all values
    print("")
    print("Selected actor:", actorname)
    print("Actor rating:", actordb.getRating(actorname))
    print("Total movies of this actor:", cnt_movies)
    print("Movies played for this actor:", cnt_played)
    print("Movies rated for this actor:", cnt_rated)


def show_stats_overall():
    """Show statistics about the movie database"""
    
    # computations inside movie array
    cnt_played, cnt_rated, cnt_hi_rated = 0, 0, 0
    for movie in moviedb.arrMovies:
        if not movie["playcount"] == 0:
            cnt_played += 1
        if movie["rating"] is not None :
            cnt_rated += 1
            if int(movie["rating"]) >= 4 :
                cnt_hi_rated += 1
    
    # computations inside actor array
    cnt_actor_unplayed, cnt_actor_hi_rated = 0, 0
    for actor in actordb.arrActors :
        cnt_movies = 0
        for movie in moviedb.arrMovies :
            if movie["actor"] == actor["name"] :
                if movie["playcount"] > 0 :
                    break
            cnt_movies += 1
        if cnt_movies >= len(moviedb.arrMovies) :
            cnt_actor_unplayed += 1
        if actor["rating"] is not None and actor["rating"] >= 4 :
            cnt_actor_hi_rated += 1
 
    # Movie stats
    print("")
    print("Total number of movies: ", len(moviedb.arrMovies))
    print("Number of movies played: ", cnt_played)
    print("Number of movies rated: ", cnt_rated)
    print("Number of hi rated movies: ", cnt_hi_rated)

    # Actor stats
    print("Total number of actors: ", len(actordb.arrActors))
    print("Number of unplayed actors: ", cnt_actor_unplayed )
    print("Number of hi rated actors: ", cnt_actor_hi_rated )


if __name__ == "__main__":
    """program entry point"""
    
    init()
    show_menu_main()
