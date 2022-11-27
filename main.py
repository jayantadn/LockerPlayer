# Import google apis
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# import standard packages
import pandas
import os.path
import configparser
import random

# import custom packages
from Utils import *
from Menu import *

# globals
config = configparser.ConfigParser()
configfile = os.path.join(os.path.dirname(__file__), "config.ini")
config.read(configfile)
df_lockerdb = pandas.DataFrame()


def gsheet_init():
    global df_lockerdb
    myprint("Loading database")
    gc = gspread.oauth(credentials_filename='credentials.json', authorized_user_filename='token.json')
    sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
    ws = sheet.get_worksheet(0)
    df_lockerdb = pandas.DataFrame(ws.get_all_records())


def play_file(idxMovie):
    # filename validation
    col = df_lockerdb.columns.get_loc('rel_path')
    rel_path = df_lockerdb.iat[idxMovie, col]
    myassert(os.path.exists(os.path.join(
        config["DEFAULT"]["MOVIEDIR"], rel_path)), "File not found")

    # increment the playcount
    col = df_lockerdb.columns.get_loc('playcount')
    df_lockerdb.iat[idxMovie, col] = df_lockerdb.iat[idxMovie, col] + 1

    # open player
    cmd = config["DEFAULT"]["PLAYER"] + " " + \
        os.path.join(config["DEFAULT"]["MOVIEDIR"], rel_path)
    os.system(cmd)

    show_menu_postplay(idxMovie)


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
            idxMovie = df_lockerdb[select].iloc[idx, 0]
            play_file(idxMovie)
            break
        elif choice == "2":  # Retry
            continue
        elif choice == "0":
            show_menu_main()
            break
        else:
            print("ERROR: Invalid choice")
            break


def play_random():
    while True:
        nrows, _ = df_lockerdb.shape
        # get a random file
        idx = random.randrange(0, nrows, 1)

        # print stats for the file
        myprint(df_lockerdb.iloc[idx])

        # # play the movie on user request
        choice = input(
            "\n1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
        if choice == "1":  # Play
            play_file(idx)
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


def show_stats_actor(actorname):
    # calculate number of movies
    select = df_lockerdb["actor"] == actorname
    col = df_lockerdb.columns.get_loc(
        'actor_rating')  # get column index from name
    cnt_movies, _ = df_lockerdb[select].shape

    # print all values
    print("")
    print("Selected actor:", actorname)
    print("Actor rating:", df_lockerdb[select].iloc[0, col])
    print("Total movies of this actor:", cnt_movies)
    print("Movies played for this actor:",
          df_lockerdb[select]['playcount'].sum())


def show_menu_postplay(idxMovie, back=False):
    menu = Menu(show_menu_main)

    actor = df_lockerdb.loc[idxMovie, 'actor']
    menu.add(MenuItem("Repeat actor", lambda: play_actor(actor)))

    def iupdate_stats():
        list_fields = df_lockerdb.columns.tolist()
        for i, field in enumerate(list_fields):
            print(i, field)
        col = int(input("Select stat to update: "))
        value = input("Enter value: ")
        if list_fields[col] == 'movie_rating':
            df_lockerdb.iat[idxMovie, col] = int(value)
        if list_fields[col] == 'actor_rating':
            col_actor = df_lockerdb.columns.get_loc(
                'actor')  # get column index from name
            actor = df_lockerdb.iat[idxMovie, col_actor]
            select = df_lockerdb['actor'] == actor
            list_select = df_lockerdb[select].index.to_list()
            arr = []
            for _ in range(len(list_select)):
                arr.append(int(value))
            df_lockerdb.loc[list_select, 'actor_rating'] = arr
        else:
            myprint(f"Cant edit field: {list_fields[col]}")
    menu.add(MenuItem("Update stats", iupdate_stats))

    # def irate_actor():
    #     actor = moviedb.arrMovies[idxMovie]["actor"]
    #     rating = input("Please enter rating for actor " + actor + " : ")
    #     actordb.rate(actor, rating)
    # menu.add(MenuItem("Rate actor", irate_actor))

    # def idelete_movie():
    #     delete = input("Are you sure to delete this movie?\n 1. Yes\t 2. No ")
    #     if delete == "1":
    #         delete_movie(rel_path)
    #     show_menu_main()  # movie index has changed, other menu items here wont work as expected
    # menu.add(MenuItem("Delete movie", idelete_movie))

    # def idelete_actor():
    #     actor = moviedb.arrMovies[idxMovie]["actor"]
    #     print("Are you sure to delete all movies of", actor, "?")
    #     delete = input("1. Yes\t 2. No ")
    #     if delete == "1":
    #         arrDelete = []
    #         for movie in moviedb.arrMovies:
    #             if movie["actor"] == actor:
    #                 if movie["rating"] is None:
    #                     arrDelete.append(movie["rel_path"])
    #                 else:
    #                     if movie["rating"] < 4:
    #                         arrDelete.append(movie["rel_path"])
    #         for rel_path in arrDelete:
    #             delete_movie(rel_path)
    #     show_menu_main()  # movie index has changed, other menu items here wont work as expected
    # menu.add(MenuItem("Delete actor", idelete_actor))

    # def iupdate_stats():
    #     entry = 1
    #     for key, val in moviedb.arrMovies[idxMovie].items():
    #         if key != "rel_path" and key != "timestamp":
    #             print(entry, key.ljust(10), val)
    #             entry += 1
    #     print(0, "Go back..")
    #     choice = int(input("Which field do you want to update: "))
    #     entry = 1
    #     for key, val in moviedb.arrMovies[idxMovie].items():
    #         if key != "rel_path" and key != "timestamp":
    #             if entry == choice:
    #                 val = input("Please enter new value for " + key + " : ")
    #                 moviedb.update(rel_path, key, val)
    #                 break
    #             entry += 1
    # menu.add(MenuItem("Update stats", iupdate_stats))

    while True:
        menu.show()
        write_database()


def show_menu_movie():
    menu = Menu()
    menu.add(MenuItem("Play a random movie", play_random))
    # menu.add( MenuItem( "Play a hi rated movie", play_rated ) )
    # menu.add( MenuItem( "Play an unrated movie", play_unrated ) )
    while True:
        menu.show()


def show_menu_actor():
    """show menu to select an actor"""

    menu = Menu()
    menu.add(MenuItem("Play selected actor", play_actor))
    menu.add(MenuItem("Play random actor", play_random_actor))
    # menu.add( MenuItem( "Play a high rated actor", play_rated_actor ) )
    # menu.add( MenuItem( "Play an unrated actor", play_unrated_actor ) )
    # menu.add( MenuItem( "Play an actor never played before", play_unplayed_actor ) )
    while True:
        menu.show()


def show_menu_main():
    menu = Menu()
    menu.add(MenuItem("Play by movie", show_menu_movie))
    menu.add(MenuItem("Play by actor", show_menu_actor))
    # menu.add( MenuItem( "Other options", show_menu_other ) )
    while True:
        menu.show()


def write_database():
    myprint("Writing database")
    gc = gspread.oauth(credentials_filename='credentials.json',
                       authorized_user_filename='token.json')
    sheet = gc.open_by_key(config['DEFAULT']['GSHEET_ID'])
    ws = sheet.get_worksheet(0)
    ws.update([df_lockerdb.columns.values.tolist()] +
              df_lockerdb.values.tolist())


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
