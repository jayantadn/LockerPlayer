#!/usr/bin/env bash

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


dir=`echo $0 | awk -F/ '{ for(i=1; i<NF; i++) printf "%s/", $i }'`
source "$dir"libDb.sh

function change_field # param = title
{
	read firstline < "$DATABASE"
	options=`echo $firstline | awk -F, '{ for(i=1; i<=NF; i++) printf "%s ", $i; printf "\n"; }'`
	
	PS3="Which field do you want to update? "
	select field in $options
	do
		read -p "Enter a value: "
		db_update "$1" "$field=$REPLY"
		break
	done
}

function menu_postplay	# parameter is file path
{
	if [ $# -lt 1 ]
	then
		echo "**ERROR** Please pass the filename as parameter to $FUNCNAME"
		exit
	fi

	title=`echo $1 | awk 'BEGIN{FS="/"} {print $NF}'`

	echo
	PS3="[Post Play] Enter your choice: "
	select item in \
		"Play another movie" \
		"Rate the movie" \
		"Delete the movie" \
		"Change other attributes" \
		"Go to main menu"
	do
		case "$item" in
			"Play another movie")
				play_random_file "$2" "$3"
				break
				;;
				
			"Rate the movie")
				read -p "Please enter a rating for the movie: "
				db_update "$title" "rating=$REPLY"
				# no break
				;;
			
			"Delete the movie")
				db_update "$title" "delete=1"
				# no break
				;;

			"Mark movie for split")
				db_update "$title" "split=1"
				# no break
				;;

			"Change other attributes")
				change_field "$title"
				echo "Going to main menu"
				break
				;;
				
			"Show movie path")
				echo $1
				# no break
				;;
				
			"Go to main menu")
				break
				;;
		esac
	done
}

# optional parameter rating. if set only high rated movies will be played.
# optional parameter "db" and alternate database.
function play_random_file
{ 
	if [ "$1" == "db" ]
	then
		db="$2"
	else
		db="$DATABASE"
	fi
	
	let max_id=`wc -l "$db" | cut -d' ' -f1`
	let max_id--
	
	while true
	do
		let play_id=$RANDOM%$max_id+1
		
		file=$MOVIE_DIR/`awk -v awk_play_id=$play_id 'BEGIN{FS=","} $1 == awk_play_id {print $7}' "$db"`
		title=`awk -v awk_play_id=$play_id 'BEGIN{FS=","} $1 == awk_play_id {print $6}' "$db"`
		
		# skip the movies marked for delete or split
		delete=`db_get "$title" "delete"`
		split=`db_get "$title" "split"`
		[ "$delete" != "0" -o "$split" != "0" ] && continue

		# filtering movies based on rating
		if [ "$1" == "rating" ]
		then
			rating=`db_get "$title" "rating"`
			[ $rating -lt 5 ] && continue
		fi

		# displaying info about the movie to be played
		awk -v awk_play_id=$play_id '
			BEGIN{FS=","} 
			
			$1 == awk_play_id {
				printf "\n\nThe following file will be played: \n Actor = %s \n Title = %s \n Category = %s \n Rating = %s \n\n ", $4, $6, $5, $2;
			}
		' "$db"

		# ask whether to play and launch the player
		read -p "Press 0 to play, 1 to try a new file or 9 to goto main menu: "
		case $REPLY in
		0)
			"$PLAYER" "$file"
			let playcount=`db_get "$title" "playcount"`
			let playcount++
			db_update "$title" "playcount=$playcount"
			menu_postplay "$file" "$1" "$2"
			break
			;;

		1)
			continue
			;;
			
		9)
			break
			;;
			
		*)
			break
			;;
		esac
	done
}

function play_random_actor
{
	if ! [ -f "$CONFIG_DIR/list_actor" ]
	then
		refresh_db
	fi

	while true
	do
		# select a random actor
		num_actors=`wc -l "$CONFIG_DIR/list_actor" | cut -d' ' -f1`
		let play_actor=$RANDOM%$num_actors+1
		actor=`sed -n ${play_actor}p "$CONFIG_DIR/list_actor"`
		
		# play the actor
		echo "Selected actor is: $actor"
		echo "Total number of movies:" `grep "$actor" "$DATABASE" | wc -l`
		echo "Number of movies played:" `grep "$actor" "$DATABASE" | awk -F, 'BEGIN{ sum=0 } { if( 0 < $3 ) sum++ } END{ print sum }'`
		read -p "Press 0 to play, 1 to try a new actor or 9 to goto main menu: "
		case $REPLY in
		0)
			db_touch "$TEMP_DIR/db_actor.csv"
            grep "$actor" "$DATABASE" >> "$TEMP_DIR/db_actor.csv"	
            serialize_id "$TEMP_DIR/db_actor.csv"	
			play_random_file "db" "$TEMP_DIR/db_actor.csv"
			unset actor
			break
			;;

		1)
			continue
			;;
			
		9)
			break
			;;
			
		*)
			break
			;;
		esac
	done
}

function play_something_else
{
	PS3="[Play Submenu] Enter your choice: "
	select item in \
		"Go to main menu"
	do
		case "$item" in
				
			"Go to main menu")
				break
				;;
		esac
	done
}


# This function will do the following:
#	- create .locker_config under home directory
#	- create default configuration
#	- set global constants
function get_config
{
	# create the config folder
	if ! [ -e ~/.locker_config ]
	then
		mkdir ~/.locker_config
	fi
	CONFIG_DIR=~/.locker_config
	
	readonly CONFIG_FILE=~/.locker_config/config.txt
	
	# create a sample config for first time usage
	if ! [ -f "$CONFIG_FILE" ]
	then
		echo "Creating initial configuration"
		
		read -p "Enter Movie Directory: "
		echo "MOVIE_DIR=$REPLY" > "$CONFIG_FILE"
		
		read -p "Enter default media player: "
		echo "PLAYER=$REPLY" >> "$CONFIG_FILE"

		echo "SPLITTER=avidemux2.6_qt4" >> "$CONFIG_FILE"
	fi
	
	# Reading configuration file
	while read line
	do
		key=`echo $line | awk 'BEGIN{FS="="} {print $1}'`
		value=`echo $line | awk 'BEGIN{FS="="} {print $2}'`
		
		case $key in
		"MOVIE_DIR")
			if ! [ -d "$value" ]
			then
				echo "**ERROR** Movie directory is not valid"
				exit
			else
				if [ `basename "$value"` != ".Locker" ] 
				then
					echo "**ERROR** Movie directory name must be .Locker" 
					exit
				else
					readonly MOVIE_DIR="$value"
				fi
			fi
			;;
			
		"PLAYER")
			which "$value" > /dev/null
			if [ $? -ne 0 ]
			then
				echo "**WARNING** Configured Movie Player is not installed"
			fi
			readonly PLAYER="$value"
			;;
			
		"SPLITTER")
			which "$value" > /dev/null
			if [ $? -ne 0 ]
			then
				echo "**WARNING** Configured splitter is not installed"
			else
				readonly SPLITTER="$value"
			fi
			;;
			
		*)
			echo "**ERROR** Configuration file corrupted"
			exit
			;;
		esac
	done < "$CONFIG_FILE"

	# create temporary folder
	readonly TEMP_DIR="$CONFIG_DIR/temp"
	[ -e "$TEMP_DIR" ] && rm -rf "$TEMP_DIR"
	mkdir "$TEMP_DIR"
	
	# database file
	readonly DATABASE="$CONFIG_DIR/database.csv"
}

function delete_non_movie_files
{
	echo "Files to be deleted: "
	echo -n > "$TEMP_DIR/list_todelete"
	
	awk -F/ '{print $0}' "$TEMP_DIR/list_fullpath" | awk -F. '
	{
		if ( NF > 1 )
			if( $NF != "m4v" && $NF != "MP4" && $NF != "f4v" && $NF != "mp4" && $NF != "mkv" && $NF != "avi" && $NF != "wmv" && $NF != "flv" && $NF != "mov" && $NF != "mpg" && $NF != "mpeg" && $NF != "264" )
				print $0;
	}' | tee -a "$TEMP_DIR/list_todelete"
	
	if [ -s "$TEMP_DIR/list_todelete" ]
	then
		read -p "Do you want to delete the above files (y/n)? "
		if [ $REPLY != "y" ]
		then
			echo "Not deleting anything"
			return
		else
			while read abs_path
			do
				rm -f -v "$abs_path"
			done < "$TEMP_DIR/list_todelete"
		fi
	else
		echo "Nothing to delete"
	fi
}

function delete_marked_movies
{
    echo "Deleting movies which were marked"
    
    # read each line to check the delete flag
    while read line 
	do
		delete=`echo "$line" | awk -F, '{print $8}'`
        
        # checking if this is the first line
        if [ "$delete" == "delete" ]
        then
            echo "$line" > "$TEMP_DIR/db_delete.csv"
            continue
        fi
        
        if [ "$delete" != "0" ]
        then
            rel_path=`echo "$line" | awk -F, '{print $7}'`
            rm -v "$MOVIE_DIR/$rel_path"
        else
            echo "$line" >> "$TEMP_DIR/db_delete.csv"
        fi
	done < "$DATABASE"

    # restoring the database file with modified one
    cp -f "$TEMP_DIR/db_delete.csv" "$DATABASE"
}

function delete_empty_folders
{
    echo "Deleting empty folders in movie directory"
    while read line 
	do
        [ -z "`ls "$line"`" ] && rmdir -v "$line"
	done < "$TEMP_DIR/list_dir"
}

# copy files to external media
function copy_files
{
	read -p "Enter destination: "
	if [ ".Locker" != `echo $REPLY | awk -F/ '{print $NF}'` ]
	then
		[ -d "$REPLY/.Locker" ] || mkdir "$REPLY/.Locker"
		DEST_DIR="$REPLY/.Locker"
	else
		DEST_DIR="$REPLY"
	fi
	echo "Destination is $DEST_DIR"
	
	max_id=`wc -l "$DATABASE" | cut -d' ' -f1`
	
	let cnt=0
	while true
	do
		let play_id=$RANDOM%$max_id
		
		rel_path=`awk -v awk_play_id=$play_id 'BEGIN{FS=","} $1 == awk_play_id {print $7}' $DATABASE`
		rel_dir=`echo $rel_path | awk -F/ '{ ORS="/"; for(i=1;i<NF;i++) print $i; }'`
		mkdir -p "$DEST_DIR/$rel_dir"
		cp -f -v "$MOVIE_DIR/$rel_path" "$DEST_DIR/$rel_dir"
		case $? in
			0)
				title=`echo $rel_path | awk -F/ '{print $NF}'`
				let cnt++
				;;
			1)
				echo "Total files copied: $cnt"
				return
				;;
			*)
				echo "**ERROR** some error has occurred during copy"
				;;
		esac
	done
}

function list_files
{
    # deleting temp files
    rm -f "$TEMP_DIR/list_lsR"
    rm -f "$TEMP_DIR/list_fullpath"
    rm -f "$TEMP_DIR/list_dir"

	# list all files recursively
	ls -a -R "$MOVIE_DIR" | sed '/total/d' > "$TEMP_DIR/list_lsR"
	
	# read lines one by one and create long path
	declare dir
	IFS=''	# this is for files which have whitespace in the beginning of name
	while read line
	do
		str=${line:0:${#MOVIE_DIR}}
		if ! [ -z "$str" ]
		then
			if [ "$str" == "$MOVIE_DIR" ]
			then
				dir=${line:0:${#line}-1}
                echo $dir >> "$TEMP_DIR/list_dir"
			else
				if ! [ -d "$dir/$line" ]
				then
					echo "$dir/$line" >> "$TEMP_DIR/list_fullpath"
				fi
			fi
		fi
		unset str
	done < "$TEMP_DIR/list_lsR"
	IFS=' '
}

function list_actors {
	echo "Creating list of actors"

	# create list of actors
	echo -n > "$TEMP_DIR/list_actor.tmp"
	echo -n > "$CONFIG_DIR/list_actor"
	while read line 
	do
		actor=`echo "$line" | awk -F, '{print $4}'`
		[ "$actor" == "actor" ] && continue # skip the first line
		grep "$actor" "$TEMP_DIR/list_actor.tmp" > /dev/null
		[ $? -ne 0 ] && echo "$actor" >> "$TEMP_DIR/list_actor.tmp"
	done < "$DATABASE"
	unset actor
	
	# sort alphabetically
	sort "$TEMP_DIR/list_actor.tmp" > "$CONFIG_DIR/list_actor"
	rm -f "$TEMP_DIR/list_actor.tmp"
}

function path_correction
{
	echo "Fixing improper path names"

	while read fullpath
	do
		echo "$fullpath" | grep '[\[,-]' > /dev/null
		if [ $? -eq 0 ]
		then
			unset partpath
			IFS='/'
			read -ra arr <<< "$fullpath"
			for part in ${arr[@]}
			do
				IFS=' '
				if ! [ -z "$part" ]
				then
					echo "$part" | grep '[\[,-]' > /dev/null
					if [ $? -eq 0 ]
					then
						oldpath="$partpath/$part"
						newpart=`echo "$part" | sed 's/["[",-]//g' | sed 's/\]//g'`
						newpath="$partpath/$newpart"
						if [ -e "$oldpath" ]
						then 
							mv -f -v "$oldpath" "$newpath"
							if [ $? -eq 0 ]
							then 
								partpath="$newpath"
							else
								echo "**ERROR** Could not rename"
								exit
							fi
						fi
					else
						partpath="$partpath/$part"
					fi
				fi
			done
		fi
	done < "$TEMP_DIR/list_fullpath"
}

function refresh_db
{
	list_files
	db_add_new_files
	update_actor_name
	remove_non_existent_files
	list_actors
}

# optional parameter db
function serialize_id
{
	echo "Serializing indices"
	
	if [ $# -eq 1 ]
	then
		dest="$1"
	else
		dest="$DATABASE"
	fi
	
	awk -F, '{
		if( cnt == 0 ) printf "index"
		else printf cnt;
		for(i=2; i<=NF; i++) printf ",%s", $i;
		printf "\n";
		cnt++;
	}' "$dest" > "$TEMP_DIR/db_serial.csv"
	
	cp -f "$TEMP_DIR/db_serial.csv" "$dest"
}

function remove_non_existent_files
{
	echo "Removing files in database which dont exist in movie dir"
	
	while read line
	do
		title=`echo "$line" | awk -F, '{print $6}'`
		[ "$title" == "title" ] && continue # ignore the first line
		rel_path=`echo "$line" | awk -F, '{print $7}'`
		abs_path="$MOVIE_DIR/$rel_path"
		[ -f "$abs_path" ] || db_remove "$rel_path"
	done < "$DATABASE"
	
	serialize_id
}

function split_movies
{
	echo "Splitting marked movies"
	while read line
	do
		split=`echo "$line" | awk -F, '{print $9}'`
		[ "$split" == "split" ] && continue # skip the first line
		if [ "$split" == "1" ]
		then
			title=`echo "$line" | awk -F, '{print $6}'`
			rel_path=`echo "$line" | awk -F, '{print $7}'`
			abs_path="$MOVIE_DIR/$rel_path"
			echo "Movie to be split: $abs_path"
			"$SPLITTER" "$abs_path"
			read -p "Do you want to delete the file (y/n)? "
            [ "$REPLY" == "y" ] && rm -f -v "$abs_path"
		fi
	done < "$DATABASE"
	
}

function update_actor_name
{
	echo "Determining actor name from file path"
	
	while read line 
	do
		flg=false
		
		echo $line | grep "Videobox" > /dev/null
		[ $? -eq 0 ] && flg=true
		
		echo $line | grep "Naughty America" > /dev/null
		[ $? -eq 0 ] && flg=true
		
		echo $line | grep "2018_begin" > /dev/null
		[ $? -eq 0 ] && flg=true

		if [ $flg == true ]
		then
			cur_actor=`echo "$line" | awk -F, '{print $4}'`
			actor=`echo "$line" | awk -F, '{ split($7, arr, "/"); print arr[2]; }'`
			title=`echo "$line" | awk -F, '{print $6}'`
			[ "$cur_actor" == "Unknown" ] && db_update "$title" "actor=$actor"
		fi
	done < "$DATABASE"
}

function rename_duplicate_movies
{
	echo "Getting rid of duplicate filenames"
	
	while read line
	do
		title=`echo "$line" | awk -F/ '{print $NF}'`
		cnt=`grep -c "$title" "$TEMP_DIR/list_fullpath"`
		if [ $cnt != "1" ]
		then
			ext=`echo "$line" | rev | cut -d'.' -f1 | rev`
			newpath=`echo "$line" | rev | cut -d'.' -f2- | rev`
			mv -v "$line" "$newpath.$RANDOM.$ext"
		fi
	done < "$TEMP_DIR/list_fullpath"
}

function fix_movie_folder
{
    if ! [ -w "$MOVIE_DIR" ] 
    then
        echo "**ERROR** No write access to $MOVIE_DIR"
        return
    fi

	# operations not needing database
	list_files
	path_correction
	delete_empty_folders
	rename_duplicate_movies
	delete_non_movie_files
	
	# operations that need database
	if [ -f "$DATABASE" ]
	then
		delete_marked_movies
		split_movies
		refresh_db
	fi
}

function backup_movies
{
	echo "Backing up high rated movies"
	
	read -p "Enter backup location: "
	backup_dest=$REPLY
	
	while read line
	do
		rating=`echo "$line" | awk -F, '{ print $2 }'`
		rel_path=`echo "$line" | awk -F, '{ print $7 }'`
		echo $rating | grep [4-9] > /dev/null
		if [ $? -eq 0 ]
		then
			rel_dir=`basename "$rel_path"`
			mkdir -p "$backup_dest/$rel_dir"
			cp -f -v "$MOVIE_DIR/$rel_path" "$backup_dest/$rel_dir"
		fi
	done < "$DATABASE"
	
	# awk -F, '{ if($2 ~ /[1-9]/) print $6 }' $DATABASE
}

function show_stats {
	echo
	echo "Total number of movies: " `wc -l "$DATABASE" | cut -d' ' -f1`
	echo "Number of movies played: " `awk -F, '{ if( 0 < $3 ) sum++ } END{ print --sum } ' "$DATABASE"` # --sum to skip the first line
	echo "Number of high rated movies: " `awk -F, '{ if( 3 < $2 ) sum++ } END{ print --sum } ' "$DATABASE"` # --sum to skip the first line
	echo
}

function menu_other
{
	echo
	PS3="[Main Menu] Enter your choice: "
	select item in \
		"Show statistics" \
		"Copy files to external media" \
		"Backup high rated movies" \
		"Sync database from external media" \
		"Go back to main menu" 
	do
		case $item in
			"Show statistics")
			show_stats
			break
			;;	

			"Copy files to external media")
			[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
			copy_files
			break
			;;	
		
		"Backup high rated movies")
			backup_movies
			break
			;;
			
		"Sync database from external media")
			read -p "Enter location where to copy from: "
			[ -f "$REPLY" ] || { echo "**ERROR** Invalid file. Check if path is Unix style. Sometimes, you simply need to try again."; return; }
			db_sync "$REPLY"            
			break
			;;
			
		"Go back to main menu")
			break
			;;
		esac
	done
}

function main
{
	# get the configuration parameters
	get_config
	echo "The following configuration is found:"
	echo -e "\tMOVIE_DIR=$MOVIE_DIR"
	echo -e "\tPLAYER=$PLAYER"
	echo -e "\tSPLITTER=$SPLITTER"

	# create backup of database
	if [ -f "$DATABASE" ]
	then
		bakdb=`date +%D | awk -F/ '{ printf "database_20%s%s%s.csv", $3, $1, $2 }'`
		dir=`dirname "$DATABASE"`
		cp -f "$DATABASE" "$dir/$bakdb"
	fi
	
	while true
	do
		echo
		PS3="[Main Menu] Enter your choice: "
		select item in \
			"Play a random file" \
			"Play a high rated movie" \
			"Play a random actor" \
			"Play something else" \
			"Refresh database" \
			"Fix movie folder" \
			"Other options" \
			"Exit" 
		do
			case $item in
				"Play a random file")
					[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
					play_random_file
					break
					;;
					
				"Play a high rated movie")
					[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
					play_random_file "rating"
					break
					;;

				"Play a random actor")
					[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
					play_random_actor
					break
					;;

				"Play something else")
					[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
					play_something_else
					break
					;;

				"Fix movie folder")
					fix_movie_folder
					break
					;;
				
				"Refresh database")
					refresh_db
					break
					;;
					
				"Other options")
					[ -f "$DATABASE" ] || { echo "**ERROR** Database file does not exist"; continue; }
					menu_other
					break
					;;
					
				"Exit")
					exit
					;;
					
				*)
					echo "Invalid option"
					;;
			esac
		done	# select
	done # while true
}

main
