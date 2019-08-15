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
import traceback

# import internal modules
from const import *
from db import DB

# global variables
CONFIG = dict()
db = DB()


# --- all function definitions ---

def copy_hi_movies():
	"""Copy high rated movies to another location"""

	try:

		# user inputs
		destdir = input( "Enter destination: " )
		rating = input( "Enter the minimum rating to copy: ")
		if not os.path.isdir(destdir) :
			print( "Please enter a valid path" ); input();	return

		# loop through the database and copy movies with high rating
		for movie in db.arrMovies:
			if movie["rating"] is not None and movie["rating"] >= int(rating):
				src = os.path.join(CONFIG["MOVIEDIR"], movie["rel_path"])
				dest = os.path.join(destdir, movie["rel_path"])
				if not os.path.exists(os.path.dirname(dest)) :
					os.makedirs(os.path.dirname(dest))
				if not os.path.exists(dest):
					print("Copying file:", movie["rel_path"])
					shutil.copy2(src, dest)

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue...")


def fix_movie_folder():
	"""fix problems in the movie folder"""

	try:
		# local variables
		arr_filename_errors = []
		arr_dirname_errors = []

		# algorithm: try to print full path of all files. If some invalid characters are found in the filename,
		# exception will be thrown. List the parent folder of such files. If parent folder name also has invalid characters,
		# print the parent of parent.
		# assumption: only movie name or movie folder names can have errors. Any other parent folder is very likely
		# manually created.

		# traverse through movie folder and check if all filenames are valid
		for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
			for file in files:
				path = os.path.join(root, file)
				try:
					print("checking filename: ", path)
				except UnicodeEncodeError:
					arr_filename_errors.append(root)

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

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue...")


def init():
	"""read the configuration file and retrieve the configuration parameters"""

	# run the script only with a password
	while True:
		passwd = input("Enter password: ")
		if not passwd == "passwd":
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
	try:

		# if no actor is specified, prompt for the actor name.
		# partial match is ok. list all actors matching the name.
		if actor is None :
			actor = input( "Actor name: " )
			arrActor = []
			for movie in db.arrMovies:
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
				print( i+1, "Exit" )
				i = int( input( "Please select an actor: " ) )
				assert 0 <= i <= len(arrActor), "Invalid input"
				if i == len(arrActor) : return # Exit
				actor = arrActor[i]

		# create array of movies by actor
		arrMovies = []
		for movie in db.arrMovies:
			if actor == movie["actor"] :
				arrMovies.append(movie)
		assert len(arrMovies) != 0, "No movies found"

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue ...")


def play_file(rel_path):
	"""play the movie and update stats"""

	idxMovie = db.getIdxMovie(rel_path)

	playcount = int(db.arrMovies[idxMovie]["playcount"]) + 1
	db.update(db.arrMovies[idxMovie]["rel_path"], "playcount", playcount)

	os.system(CONFIG["PLAYER"] + " " + os.path.join(CONFIG["MOVIEDIR"],
		db.arrMovies[idxMovie]["rel_path"]))

	# post play menu
	post_play = input(
		"1. Rate\t 2. Delete\t 0. Go back \nEnter your choice: ")

	if post_play == "1":
		rating = input("Enter your rating: ")
		db.update(db.arrMovies[idxMovie]["rel_path"], "rating", rating)

	elif post_play == "2":
		delete = input("Are you sure to delete this movie?\n 1. Yes\t 2. No ")
		if delete == "1":
			db.update(db.arrMovies[idxMovie]["rel_path"], "delete", True)

	elif post_play == "0":
		return

	else:
		print("ERROR: Invalid choice")
		return


def play_random() :
	try:
		assert len(db.arrMovies) > 0, \
			"[ERROR] No movies found"

		while True:
			# get a random file
			idx = random.randrange(0, len(db.arrMovies), 1)

			# print stats for the file
			print("\nWe found the following movie for you:")
			print("actor = ", db.arrMovies[idx]["actor"])
			print("title = ", os.path.basename(db.arrMovies[idx]["rel_path"]))
			print("category = ", db.arrMovies[idx]["category"])
			print("rating = ", db.arrMovies[idx]["rating"])

			# print stats for actor
			actor = db.arrMovies[idx]["actor"]
			if actor is not None and not actor == "Unknown":
				cnt_movies = 0
				cnt_played = 0
				for movie in db.arrMovies:
					if movie["actor"] == actor:
						cnt_movies += 1
						cnt_played += int(movie["playcount"])
				print("Total movies of this actor: ", cnt_movies)
				print("Movies played of this actor: ", cnt_played)

			choice = input( "1. Play\t 2. Retry\t 0. Main menu \nEnter your choice: ")
			if choice == "1":
				play_file(db.arrMovies[idx]["rel_path"])

			elif choice == "2":
				continue

			elif choice == "0" :
				break

			else :
				print( "ERROR: Invalid choice" )
				break

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue...")


def refresh_db():
	"""traverse movie folder and update the database"""

	try:
		# remove any invalid entries
		db.cleanup()

		# check for non-existent entries in database
		for movie in db.arrMovies:
			full_path = os.path.join(CONFIG["MOVIEDIR"], movie["rel_path"])
			if not os.path.exists(full_path):
				db.remove(movie["rel_path"])

		# add any new files
		for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]):
			for file in files:
				# check for file extension
				ext = os.path.splitext(file)[1]
				if ext not in EXTLIST:
					continue

				# add to database if not exist already
				path = os.path.join(root, file)
				rel_path = path[len(CONFIG["MOVIEDIR"])::][1:]
				if not db.exists(rel_path):
					db.add(rel_path)

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue...")


def show_menu():
	"""show the main menu"""
	menu_main = ConsoleMenu("Main menu")
	menu_main.append_item( FunctionItem("Play a random file", play_random) )
	menu_main.append_item( FunctionItem("Play by actor", play_actor) )

	menu_other = ConsoleMenu("Other options")
	menu_other.append_item(FunctionItem("Refresh database", refresh_db))
	menu_other.append_item(FunctionItem("Fix movie folder", fix_movie_folder))
	menu_other.append_item(FunctionItem("Show statistics", show_stats))
	menu_other.append_item(FunctionItem("Copy high rated movies", copy_hi_movies))

	item_other = SubmenuItem("Other options", menu_other, menu_main)
	menu_main.append_item(item_other)
	menu_main.show()


def show_stats():
	"""Show statistics about the movie database"""
	try:
		cnt_played, cnt_high_rated = 0, 0
		for movie in db.arrMovies:
			if not movie["playcount"] == 0:
				cnt_played += 1
			if movie["rating"] is not None and int(movie["rating"]) >= 4:
				cnt_high_rated += 1
		print("Total number of movies: ", len(db.arrMovies))
		print("Number of movies played: ", cnt_played)
		print("Number of high rated movies: ", cnt_high_rated)

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	input("\nPress <enter> to continue...")


def main():
	"""program entry point"""
	init()
	show_menu()


# invoke the main
main()
