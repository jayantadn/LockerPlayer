# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# import standard packages
import pandas as pd
import os.path
import configparser
import random
from datetime import datetime
import time
from send2trash import send2trash

# import custom packages
from utils import *
from menu import *
from const import *

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)
df_lockerdb = pd.DataFrame()


def gsheet_init():
    global df_lockerdb
    myprint("Loading database")

    if not (os.path.exists(os.path.join(CURDIR, 'credentials.json')) or os.path.exists(os.path.join(CURDIR, 'token.json'))):
        print("ERROR: 'credentials.json' or 'token.json' does not exist")
        print("Please download the google credentials to the current path")
        exit(1)

    try:
        gc = gspread.oauth(credentials_filename='credentials.json',
                           authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
    except:
        os.remove(os.path.join(CURDIR, 'token.json'))
        gc = gspread.oauth(credentials_filename='credentials.json',
                           authorized_user_filename='token.json')
        sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])

    ws = sheet.get_worksheet(0)
    df_lockerdb = pd.DataFrame(ws.get_all_records())

    # reset the index
    df_lockerdb.set_index('rel_path', inplace=True)

    # treat data types
    df_lockerdb.playcount = pd.to_numeric(df_lockerdb.playcount)
    df_lockerdb.movie_rating = pd.to_numeric(df_lockerdb.movie_rating)
    df_lockerdb.actor_rating = pd.to_numeric(df_lockerdb.actor_rating)


def fix_movie_folder():
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
    for root, subdirs, files in os.walk(config['DEFAULT']['MOVIEDIR']):
        if len(subdirs) + len(files) == 0:
            arrEmptyFolders.append(root)

        for file in files:
            path = os.path.join(root, file)
            try:
                # extract the relative path
                rel_path = path[len(config['DEFAULT']['MOVIEDIR'])::][1:]

                # mark non movie files for delete
                ext = os.path.splitext(path)[1]
                if ext not in EXTLIST:
                    arrDelete.append(rel_path)

                # convert actor name to title case
                folder1 = None
                folder2 = None
                head = path
                while True:
                    head, tail = os.path.split(head)
                    folder2 = folder1
                    folder1 = tail
                    if head == config['DEFAULT']['MOVIEDIR']:
                        break
                actor = folder2
                if actor != actor.title():
                    partpath = path[: path.find(actor) + len(actor)]
                    if partpath not in arrCase:
                        arrCase.append(partpath)

            except UnicodeEncodeError:
                arr_filename_errors.append(root)

    # delete all empty folders
    if len(arrEmptyFolders) > 0:
        for folder in arrEmptyFolders:
            print(folder)
        confirm = input(
            "\nThe above folders are empty and will be removed. Please confirm (y/n): ")
        if confirm == "y":
            for folder in arrEmptyFolders:
                os.rmdir(folder)

    # display the filename and dirname errors
    if len(arr_filename_errors) > 0:
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
    elif len(arrDelete) > 0:
        for file in arrDelete:
            print(file)
        confirm = input(
            "\nThe above file are not movies and will be removed. Please confirm (y/n): ")
        if confirm == "y":
            for rel_path in arrDelete:
                send2trash(os.path.join(
                    config['DEFAULT']["MOVIEDIR"], rel_path))

    # change actor names to title case
    elif len(arrCase) > 0:
        print("The following path need to be changed to title case:")
        for partpath in arrCase:
            print(partpath)
        cont = input("Do you want to continue?\n 1. Yes\t 2. No ")
        if cont == "1":
            # renaming first with _ suffix as windows does not allow
            # case change in filename
            for partpath in arrCase:
                src = partpath
                head, tail = os.path.split(partpath)
                dest = os.path.join(head, tail.title())

                os.rename(src, dest + "_")
                print("Renaming file: ", src)
                time.sleep(1)
            for partpath in arrCase:
                head, tail = os.path.split(partpath)
                src = os.path.join(head, tail.title() + "_")
                os.rename(src, src[:-1])

    else:
        print("\nNo errors found in movie folder")


def add_movie(rel_path):
    global df_lockerdb
    print("Adding to database:", rel_path)

    # finding the actor name. Its basically the second folder from rel_path
    folder1 = None
    folder2 = None
    head = rel_path

    while True:
        head, tail = os.path.split(head)
        folder2 = folder1
        folder1 = tail
        if len(head) == 0:
            break
    actor = folder2

    # create the entry
    df = pd.DataFrame({
        "rel_path": [rel_path],
        "movie_rating": [0],
        "actor_rating": [get_actor_rating(actor)],
        "playcount": [0],
        "actor": [actor],
        "category": ["Straight"],
        "studio": [rel_path.split("\\")[0]],
        # "timestamp": [datetime.now().strftime("%Y-%m-%d_%H:%M:%S")]
    })
    df.set_index('rel_path', inplace=True)
    df_lockerdb = pd.concat([df_lockerdb, df])


def refresh_db():
    fix_movie_folder()

    # check for non-existent entries in database
    arrDelete = []
    for rel_path in df_lockerdb.index.to_list():
        full_path = os.path.join(config['DEFAULT']["MOVIEDIR"], rel_path)
        if not os.path.exists(full_path):
            arrDelete.append(rel_path)
    if len(arrDelete) > 0:
        for rel_path in arrDelete:
            print(rel_path)
        delete = input(
            "The above files are not found in filesystem. Remove them from database?\n 1. Yes\t 2. No ")
        if delete == "1":
            for rel_path in arrDelete:
                df_lockerdb.drop(rel_path, inplace=True)
            print("Done removing files")

    # add any new files
    for root, subdirs, files in os.walk(config['DEFAULT']["MOVIEDIR"]):
        for file in files:
            # add to database if not exist already
            # assuming non-movie files are already deleted
            path = os.path.join(root, file)
            rel_path = path[len(config['DEFAULT']["MOVIEDIR"])::][1:]
            if rel_path not in df_lockerdb.index.to_list():
                add_movie(rel_path)

    write_database()
    print("\nDatabase refresh completed.")


def play_movie(rel_path):
    # filename validation
    full_path = os.path.join(config["DEFAULT"]["MOVIEDIR"], rel_path)
    if not os.path.exists(full_path):
        print(f"File not found: {full_path}")
        return

    # increment the playcount
    df_lockerdb.at[rel_path,
                   'playcount'] = int(df_lockerdb.at[rel_path, 'playcount']) + 1

    # open player
    player = config["DEFAULT"]["PLAYER"]
    # myassert(os.path.exists(player), "Movie player not found") #FIXME: unable to handle path with spaces
    movie = os.path.join(config['DEFAULT']['MOVIEDIR'], rel_path)
    print(f"Playing movie: {movie}")
    cmd = f"{player} " + movie
    os.system(cmd)

    show_menu_postplay(rel_path)


# Play movies for a given actor. If no actor specified, prompt for one.
def play_actor(actor=None):
    # generate list of actors
    list_actors = df_lockerdb['actor'].drop_duplicates().to_list()

    # if no actor is specified, prompt for the actor name.
    # partial match is ok. list all actors matching the name.
    if actor is None:
        a = input("Actor name: ")
        arrActor = []
        for al in list_actors:
            if a in al and al not in arrActor:
                arrActor.append(al)

        # If no match, throw error
        # if single match, then trouble free
        # if multiple match, then prompt to select one
        assert len(arrActor) != 0, "No such actor found"
        if len(arrActor) == 1:
            actor = arrActor[0]
        else:
            for i, actor in enumerate(arrActor):
                print(i, actor)
            print(i+1, "Go back")
            i = int(input("Please select an actor: "))
            assert 0 <= i <= len(arrActor), "Invalid input"
            if i == len(arrActor):
                return  # Go back
            actor = arrActor[i]

    # select a random movie for the actor
    select = df_lockerdb['actor'] == actor
    while True:
        nrows, _ = df_lockerdb[select].shape
        # get a random file
        idx = random.randrange(0, nrows, 1)

        # print stats for the file
        myprint(df_lockerdb[select].iloc[idx])

        # # play the movie on user request
        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":  # Play
            rel_path = df_lockerdb[select].iloc[idx].name
            play_movie(rel_path)
            break
        elif choice == "2":  # Retry
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break

def play_something():
    arr = [ play_random_actor, play_random_movie, play_rated_actor, play_rated_movie, 
            play_unrated_actor, play_unrated_movie, play_random_studio, play_category] 
    idx = random.randint(0, len(arr)-1)
    arr[idx]()

def play_rated_movie() :
    print("\nPlay a high rated movie")

    # create a list of movies with at least given rating
    select = pd.to_numeric(df_lockerdb['movie_rating']) >= MINRATING
    arrMovies = df_lockerdb[select].index.to_list()

    # randomize and play movie from the list
    while True:
        idx = random.randint(0, len(arrMovies)-1)
        movie = arrMovies[idx]
        if movie is not None and not movie == "Unknown":
            show_stats_movie(movie)

        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        
        if choice == "1":
            play_movie(movie)

        elif choice == "2":
            continue

        elif choice == "0":
            show_menu_main()
            break

        else:
            print("ERROR: Invalid choice")
            break

def play_unrated_movie() :
    print("\nPlay a unrated movie")

    # create a list of movies with no rating
    select = pd.to_numeric(df_lockerdb['movie_rating']) == 0
    arrMovies = df_lockerdb[select].index.to_list()

    # randomize and play movie from the list
    while True:
        idx = random.randint(0, len(arrMovies)-1)
        movie = arrMovies[idx]
        if movie is not None and not movie == "Unknown":
            show_stats_movie(movie)

        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        
        if choice == "1":
            play_movie(movie)

        elif choice == "2":
            continue

        elif choice == "0":
            show_menu_main()
            break

        else:
            print("ERROR: Invalid choice")
            break


def play_random_movie():
    print("\nPlay a random movie")

    while True:
        nrows, _ = df_lockerdb.shape
        # get a random file
        idx = random.randrange(0, nrows, 1)

        # print stats for the file
        show_stats_movie(df_lockerdb.iloc[idx].name)

        # play the movie on user request
        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":  # Play
            play_movie(df_lockerdb.iloc[idx].name)
            break
        elif choice == "2":  # Retry
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break


def play_random_actor():
    print("\nPlay a random actor")

    list_actors = df_lockerdb['actor'].drop_duplicates().to_list()

    while True:
        idx = random.randrange(0, len(list_actors), 1)
        actor = list_actors[idx]
        if actor is not None and not actor == "Unknown":
            show_stats_actor(actor)

        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_actor(actor)
        elif choice == "2":
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break


def play_rated_actor():
    print("\nPlay movie for a high rated actor")

    # create a list of actors with at least given rating
    select = pd.to_numeric(df_lockerdb['actor_rating']) >= MINRATING
    actorlist = df_lockerdb[select]['actor'].unique()

    # randomize and play actor from the list
    while True:
        idx = random.randint(0, len(actorlist)-1)
        actor = actorlist[idx]
        if actor is not None and not actor == "Unknown":
            show_stats_actor(actor)

        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_actor(actor)

        elif choice == "2":
            continue

        elif choice == "0":
            show_menu_main()
            break

        else:
            print("ERROR: Invalid choice")
            break

def play_unrated_actor():
    print("\nPlay movie for a unrated actor")

    # create a list of actors with at least given rating
    select = pd.to_numeric(df_lockerdb['actor_rating']) == 0
    actorlist = df_lockerdb[select]['actor'].unique()

    # randomize and play actor from the list
    while True:
        idx = random.randint(0, len(actorlist)-1)
        actor = actorlist[idx]
        if actor is not None and not actor == "Unknown":
            show_stats_actor(actor)

        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":
            play_actor(actor)

        elif choice == "2":
            continue

        elif choice == "0":
            show_menu_main()
            break

        else:
            print("ERROR: Invalid choice")
            break

# Play movies for a given studio. If no studio specified, prompt for one.
def play_studio(studio=None):
    # generate list of studios
    arrstudio = df_lockerdb['studio'].drop_duplicates().to_list()

    # if no studio is specified, prompt for the studio name.
    if studio is None:
        assert len(arrstudio) != 0, "No such studio found"
        for i, studio in enumerate(arrstudio):
            print(i+1, studio)
        print(0, "Go back")
        i = int(input("Please select an studio: ")) - 1
        assert -1 <= i < len(arrstudio), "Invalid input"
        if i == -1:
            return  # Go back
        studio = arrstudio[i]

    # select a random movie for the studio
    select = df_lockerdb['studio'] == studio
    while True:
        nrows, _ = df_lockerdb[select].shape
        # get a random file
        idx = random.randrange(0, nrows, 1)

        # print stats for the file
        myprint(df_lockerdb[select].iloc[idx])

        # play the movie on user request
        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":  # Play
            rel_path = df_lockerdb[select].iloc[idx].name
            play_movie(rel_path)
            break
        elif choice == "2":  # Retry
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break

# Play movies for a given studio. If no studio specified, prompt for one.
def play_category(category=None):
    # generate list of category
    arrcategory = df_lockerdb['category'].drop_duplicates().to_list()

    # if no category is specified, select a random category
    if category is None:
        assert len(arrcategory) != 0, "No such category found"
        idx = random.randint(0, len(arrcategory)-1)
        assert 0 <= idx < len(arrcategory), "Invalid input"
        category = arrcategory[idx]

    print(f"\nSelected category is {category}")

    # select a random movie for the category
    select = df_lockerdb['category'] == category
    while True:
        nrows, _ = df_lockerdb[select].shape
        # get a random file
        idx = random.randrange(0, nrows, 1)

        # print stats for the file
        myprint(df_lockerdb[select].iloc[idx])

        # play the movie on user request
        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":  # Play
            rel_path = df_lockerdb[select].iloc[idx].name
            play_movie(rel_path)
            break
        elif choice == "2":  # Retry
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break


def play_random_studio():
    print("\nPlay a random studio")

    list_studios = df_lockerdb['studio'].drop_duplicates().to_list()

    while True:
        idx = random.randrange(0, len(list_studios), 1)
        studio = list_studios[idx]
        print(f"Selected studio is: {studio}")
        play_studio(studio)

def show_stats_actor(actorname):
    # calculate number of movies
    select = df_lockerdb["actor"] == actorname
    col = df_lockerdb.columns.get_loc(
        'actor_rating')  # get column index from name
    cnt_movies, _ = df_lockerdb[select].shape

    # print all values
    print("Selected actor:", actorname)
    actor_rating = df_lockerdb[select].iloc[0, col]
    print("Actor rating:", actor_rating)
    print("Total movies of this actor:", cnt_movies)
    print("Movies played for this actor:",
          df_lockerdb[select]['playcount'].sum())

def show_stats_movie(rel_path):
    # print all values
    print("Selected movie:", os.path.basename(rel_path))
    print("Movie rating:", df_lockerdb.at[rel_path, 'movie_rating'])
    print("Actor:", df_lockerdb.at[rel_path, 'actor'])
    print("Category:", df_lockerdb.at[rel_path, 'category'])
    print("Studio:", df_lockerdb.at[rel_path, 'studio'])

def get_actor_rating(actorname):
    select = df_lockerdb["actor"] == actorname
    col = df_lockerdb.columns.get_loc(
        'actor_rating')  # get column index from name
    nrows, _ = df_lockerdb[select].shape
    if nrows == 0:
        actor_rating = 0
    else:
        actor_rating = df_lockerdb[select].iloc[0, col]
        if actor_rating == "":
            actor_rating = 0
    return actor_rating


def delete_movie(rel_path):
    print("deleting file: ", rel_path)
    send2trash(os.path.join(config['DEFAULT']["MOVIEDIR"], rel_path))
    try:
        df_lockerdb.drop(rel_path, inplace=True)
    except:
        print("ERROR: Cant delete file from database")


def show_menu_postplay(rel_path, back=False):
    menu = Menu(show_menu_main)

    actor = df_lockerdb.at[rel_path, 'actor']
    menu.add(MenuItem("Repeat actor", lambda: play_actor(actor)))

    def iupdate_stats():
        list_fields = df_lockerdb.columns.tolist()
        for i, field in enumerate(list_fields):
            print(i, field)
        col = int(input("\nSelect stat to update: "))
        
        if list_fields[col] == 'movie_rating':
            value = input("Enter value: ")
            df_lockerdb.at[rel_path, 'movie_rating'] = int(value)
        elif list_fields[col] == 'actor_rating':
            value = input("Enter value: ")
            actor = df_lockerdb.at[rel_path, 'actor']
            select = df_lockerdb['actor'] == actor
            list_select = df_lockerdb[select].index.to_list()
            arr = []
            for _ in range(len(list_select)):
                arr.append(int(value))
            df_lockerdb.loc[list_select, 'actor_rating'] = arr
        if list_fields[col] == 'studio':
            arrstudio = df_lockerdb['studio'].drop_duplicates().to_list()
            for i, studio in enumerate(arrstudio):
                print(i+1, studio)
            print(0, "Something else")
            i = int(input("Please select an studio: ")) - 1
            assert -1 <= i < len(arrstudio), "Invalid input"
            if i == -1:
                studio = input("Enter studio name: ")
            else:
                studio = arrstudio[i]            
            df_lockerdb.at[rel_path, 'studio'] = studio
        if list_fields[col] == 'category':
            arrcategory = df_lockerdb['category'].drop_duplicates().to_list()
            for i, category in enumerate(arrcategory):
                print(i+1, category)
            print(0, "Something else")
            i = int(input("Please select an category: ")) - 1
            assert -1 <= i < len(arrcategory), "Invalid input"
            if i == -1:
                category = input("Enter category name: ")
            else:
                category = arrcategory[i]            
            df_lockerdb.at[rel_path, 'category'] = category
        else:
            myprint(f"Cant edit field: {list_fields[col]}")
    menu.add(MenuItem("Update stats", iupdate_stats))

    def idelete_movie():
        delete = input("Are you sure to delete this movie?\n 1. Yes\t 2. No ")
        if delete == "1":
            delete_movie(rel_path)
    menu.add(MenuItem("Delete movie", idelete_movie))

    def idelete_actor():
        print("Are you sure to delete all movies of", actor, "?")
        delete = input("1. Yes\t 2. No ")
        if delete == "1":
            # FIXME: exclude movies with high rating
            select = df_lockerdb['actor'] == actor
            arrDelete = df_lockerdb[select].index.to_list()
            for idx in arrDelete:
                delete_movie(idx)
    menu.add(MenuItem("Delete actor", idelete_actor))

    while True:
        menu.show()
        write_database()


def show_menu_movie():
    menu = Menu()
    menu.add(MenuItem("Play a random movie", play_random_movie))
    menu.add( MenuItem( "Play a hi rated movie", play_rated_movie ) )
    menu.add( MenuItem( "Play an unrated movie", play_unrated_movie ) )
    while True:
        menu.show()


def show_menu_actor():
    """show menu to select an actor"""

    menu = Menu()
    menu.add(MenuItem("Play random actor", play_random_actor))
    menu.add(MenuItem("Play selected actor", play_actor))
    menu.add(MenuItem("Play a high rated actor", play_rated_actor))
    menu.add( MenuItem( "Play an unrated actor", play_unrated_actor ) )
    # menu.add( MenuItem( "Play an actor never played before", play_unplayed_actor ) )
    while True:
        menu.show()


def show_menu_studio():
    """show menu to select a studio"""

    menu = Menu(show_menu_main)
    menu.add(MenuItem("Play random studio", play_random_studio))
    menu.add(MenuItem("Play selected studio", play_studio))
    menu.add(MenuItem("Play random category", play_category))
    while True:
        menu.show()

def show_menu_other():
    """show menu which could not fit into main menu"""

    menu = Menu(show_menu_main)
    menu.add(MenuItem("Refresh database", refresh_db))
    menu.add(MenuItem("Show overall statistics", show_stats_overall))
    # menu.add( MenuItem( "Copy high rated movies", copy_hi_movies ) )
    # menu.add( MenuItem( "Show play history", show_play_history ) )
    menu.add( MenuItem( "Update studio information", update_studio ) )
    while True:
        menu.show()


def show_stats_overall():
    # movie statistics
    cnt_movies, _ = df_lockerdb.shape
    cnt_played, _ = df_lockerdb[df_lockerdb.playcount > 0].shape
    cnt_rated, _ = df_lockerdb[df_lockerdb.movie_rating > 0].shape
    cnt_hi_rated, _ = df_lockerdb[df_lockerdb.movie_rating > 3].shape

    # computations inside actor array
    s_all_actors = df_lockerdb.actor.unique()
    s_played_actors = df_lockerdb[df_lockerdb.playcount > 0].actor.unique()
    cnt_actors = s_all_actors.size
    cnt_actor_hi_rated = df_lockerdb[df_lockerdb.actor_rating > 4].actor.unique(
    ).size
    cnt_actor_unplayed = s_all_actors.size - s_played_actors.size
    # compute unplayed actor

    # cnt_actor_unplayed, cnt_actor_hi_rated = 0, 0
    # for actor in actordb.arrActors:
    #     cnt_movies = 0
    #     for movie in moviedb.arrMovies:
    #         if movie["actor"] == actor["name"]:
    #             if movie["playcount"] > 0:
    #                 break
    #         cnt_movies += 1
    #     if cnt_movies >= len(moviedb.arrMovies):
    #         cnt_actor_unplayed += 1
    #     if actor["rating"] is not None and actor["rating"] >= 4:
    #         cnt_actor_hi_rated += 1

    # Movie stats
    print("\n---Movie stats---")
    print("Total number of movies: ", cnt_movies)
    print("Number of movies played: ", cnt_played)
    print("Number of movies rated: ", cnt_rated)
    print("Number of hi rated movies: ", cnt_hi_rated)

    # Actor stats
    print("---Actor stats---")
    print("Total number of actors: ", cnt_actors)
    print("Number of hi rated actors: ", cnt_actor_hi_rated)
    print("Number of unplayed actors: ", cnt_actor_unplayed)


def show_menu_main():
    menu = Menu()
    menu.add(MenuItem("Play something", play_something))
    menu.add(MenuItem("Play by movie", show_menu_movie))
    menu.add(MenuItem("Play by actor", show_menu_actor))
    menu.add(MenuItem("Play by studio", show_menu_studio))
    menu.add(MenuItem("Other options", show_menu_other))
    while True:
        menu.show()


def update_studio():
    global df_lockerdb
    
    print("Updating studio information")
    s_studio = df_lockerdb.index.map(lambda x: x.split("\\")[0])
    df_lockerdb['studio'] = s_studio
    write_database()


def write_database():
    global df_lockerdb

    myprint("Writing database")
    gc = gspread.oauth(credentials_filename='credentials.json',
                       authorized_user_filename='token.json')
    sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
    ws = sheet.get_worksheet(0)

    # retreat data types
    df_lockerdb.playcount = df_lockerdb.playcount.map(lambda x: str(x))
    df_lockerdb.movie_rating = df_lockerdb.movie_rating.map(lambda x: str(x))
    df_lockerdb.actor_rating = df_lockerdb.actor_rating.map(lambda x: str(x))
    df_lockerdb = df_lockerdb.fillna('')

    # reset index
    _df_lockerdb = df_lockerdb.reset_index(names='rel_path')

    # write to server
    ws.update([_df_lockerdb.columns.values.tolist()] +
              _df_lockerdb.values.tolist())


def main():
    gsheet_init()
    show_menu_main()


if __name__ == "__main__":
    try:
        main()
    except (SystemExit, KeyboardInterrupt) as e:
        pass
    except:
        myassert(False, "An exception has occurred.", True)
