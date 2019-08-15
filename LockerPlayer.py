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
from send2trash import send2trash
import getpass

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
		rating = input( "Enter the minimum rating: ")
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


def delete_movie(rel_path) :
	send2trash(os.path.join(CONFIG["MOVIEDIR"], rel_path))
	db.remove(rel_path)


def fix_movie_folder():
	"""fix problems in the movie folder"""

	# strategy: fix movie folder should only fix problems in the movie folder.
	# It should not touch the database.
	# However, its always best to refresh the database immediately afterwards

	try:
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
		for root, subdirs, files in os.walk(CONFIG["MOVIEDIR"]) :
			for file in files:
				path = os.path.join(root, file)
				try:

					# extract the relative path
					rel_path = path[len(CONFIG["MOVIEDIR"])::][1:]

					# invalid filename will throw exception
					# print("checking filename: ", path)

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
				# if database was updated before fixing the movie folder,
				# this api will delete the movie from database also.
				# Although its expected that fix and rebuild_db should be
				# independent of each other.
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

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	print( "Finished fixing movie folder. Advise to refresh database next" )
	input("\nPress <enter> to continue...")


def init():
	"""read the configuration file and retrieve the configuration parameters"""

	# run the script only with a password
	while True:
		passwd = getpass.getpass()
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
				print( i+1, "Go back" )
				i = int( input( "Please select an actor: " ) )
				assert 0 <= i <= len(arrActor), "Invalid input"
				if i == len(arrActor) : return # Go back
				actor = arrActor[i]

		# create array of movies by actor. give movie array to randomize
		arrMovies = []
		for movie in db.arrMovies:
			if actor == movie["actor"] :
				arrMovies.append(movie)
		assert len(arrMovies) != 0, "No movies found"
		play_random(arrMovies)

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()
		input("\nPress <enter> to continue ...")


def play_rated() :
	"""Play a high rated movie"""
	rating = int( input("Enter the minimum rating: ") )
	arrMovies = []
	for movie in db.arrMovies :
		if movie["rating"] is not None and movie["rating"] >= rating :
			arrMovies.append(movie)
	play_random(arrMovies)


def play_unrated() :
	"""Play an unrated movie"""
	arrMovies = []
	for movie in db.arrMovies :
		if movie["rating"] is None :
			arrMovies.append(movie)
	play_random(arrMovies)


def play_file(rel_path):
	"""play the movie and update stats"""

	assert os.path.exists( os.path.join(CONFIG["MOVIEDIR"], rel_path) ), "File not found"

	idxMovie = db.getIdxMovie(rel_path)

	playcount = int(db.arrMovies[idxMovie]["playcount"]) + 1
	db.update(db.arrMovies[idxMovie]["rel_path"], "playcount", playcount)

	os.system(CONFIG["PLAYER"] + " " + os.path.join(CONFIG["MOVIEDIR"],
		db.arrMovies[idxMovie]["rel_path"]))

	# post play menu
	post_play = input(
		"1. Rate  2. Repeat actor  3. Update stats  4. Delete movie  "
		"5. Delete actor  0. Go back \nEnter your choice: ")

	if post_play == "1":	# rating
		rating = input("Enter your rating: ")
		db.update(db.arrMovies[idxMovie]["rel_path"], "rating", rating)

	elif post_play == "2":	# repeat actor
		play_actor( db.arrMovies[idxMovie]["actor"] )

	elif post_play == "3":	# update stats
		print( "Current stats:" )
		for key, val in db.arrMovies[idxMovie].items() :
			if key != "rel_path":
				print( key.ljust(10), val )
		print( "0".ljust(10), "Go back" )
		key = input( "Which field do you want to update: " )
		if key != "0" :
			val = input( "Please enter new value: " )
			db.update( rel_path, key, val )

	elif post_play == "4":	# delete movie
		delete = input("Are you sure to delete this movie?\n 1. Yes\t 2. No ")
		if delete == "1":
			delete_movie(rel_path)

	elif post_play == "5":  # delete actor
		actor = db.arrMovies[idxMovie]["actor"]
		print( "Are you sure to delete all movies of", actor, "?" )
		delete = input( "1. Yes\t 2. No " )
		if delete == "1" :
			arrDelete = []
			for movie in db.arrMovies :
				if movie["actor"] == actor :
					arrDelete.append(movie["rel_path"])
			for rel_path in arrDelete :
				delete_movie(rel_path)

	elif post_play == "0":
		return

	else:
		print("ERROR: Invalid choice")

	input("\nPress <enter> to continue...")


def play_random(arrMovies = db.arrMovies) :
	try:

		assert len(arrMovies) > 0, \
			"[ERROR] No movies found"

		while True:
			# get a random file
			idx = random.randrange(0, len(arrMovies), 1)

			# print stats for the file
			print("\nWe found the following movie for you:")
			print("actor = ", arrMovies[idx]["actor"])
			print("title = ", os.path.basename(arrMovies[idx]["rel_path"]))
			print("category = ", arrMovies[idx]["category"])
			print("rating = ", arrMovies[idx]["rating"])

			# print stats for actor
			actor = arrMovies[idx]["actor"]
			if actor is not None and not actor == "Unknown":
				cnt_movies = 0
				cnt_played = 0
				for movie in arrMovies:
					if movie["actor"] == actor:
						cnt_movies += 1
						cnt_played += int(movie["playcount"])
				print("Total movies of this actor: ", cnt_movies)
				print("Movies played of this actor: ", cnt_played)

			choice = input( "1. Play\t 2. Retry\t 0. Go back \nEnter your choice: ")
			if choice == "1":
				play_file(arrMovies[idx]["rel_path"])

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

	# strategy: refresh_db should only modify the database.
	# It should not touch the movie folder.

	try:

		# change actor names to title case
		for movie in db.arrMovies :
			if movie["actor"] != movie["actor"].title() :
				rel_path_new = movie["rel_path"].replace( movie["actor"],
					movie["actor"].title(), 1 )
				if os.path.exists( os.path.join(CONFIG["MOVIEDIR"], rel_path_new) ) :
					db.update(movie["rel_path"], "rel_path", rel_path_new)
					db.update(movie["rel_path"], "actor", movie["actor"].title())

		# check for non-existent entries in database
		arrDelete = []
		for movie in db.arrMovies:
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
				if not db.exists(rel_path):
					db.add(rel_path)

	# forced to use bare except because consolemenu is not showing any exception
	except:
		traceback.print_exc()

	print( "\nDatabase refresh completed." )
	input("\nPress <enter> to continue...")


def show_menu():
	"""show the main menu"""
	menu_main = ConsoleMenu("Main menu")
	menu_main.append_item( FunctionItem("Play a random file", play_random) )
	menu_main.append_item( FunctionItem("Play unrated movie", play_unrated) )
	menu_main.append_item( FunctionItem("Play a high rated movie", play_rated) )
	menu_main.append_item( FunctionItem("Play by actor", play_actor) )

	menu_other = ConsoleMenu("Other options")
	menu_other.append_item(FunctionItem("Fix movie folder", fix_movie_folder))
	menu_other.append_item(FunctionItem("Refresh database", refresh_db))
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
