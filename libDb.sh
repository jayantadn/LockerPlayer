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

movie_ext_arr=("m4v" "f4v" "mp4" "MP4" "mkv" "avi" "wmv" "flv" "mov" "mpg" "mpeg" "264")

# param = title, rel_path
function db_add 
{
	if [ $# -eq 0 ]
	then
		echo "Please provide proper arguments to $FUNCNAME"
		return
	else
		ext=`echo $1 | rev | cut -d"." -f1 | rev`
		for var in ${movie_ext_arr[*]}
		do
			if [ "$var" == "$ext" ]
			then
				echo "Adding to database: $2"
				let max_id++
				echo "$max_id,0,0,Unknown,Straight,$1,$2,0,0" >> "$DATABASE"				
			fi
		done
	fi
}

function db_add_new_files
{
	# create/update the database.csv
	if ! [ -e "$DATABASE" ]
	then
		echo "Movie database does not exist. Will create it now."
		db_touch
		let max_id=0
		while read line
		do
			title=`echo "$line" | awk 'BEGIN { FS="/" } {print $NF}'`
			rel_path=`echo "${line:${#MOVIE_DIR}+1:${#line}}"`
			db_add "$title" "$rel_path"
		done < "$TEMP_DIR/list_fullpath"
	else
		echo "Database file already exists"
		echo "Updating database"
		let max_id=`wc -l "$DATABASE" | cut -d' ' -f1` && let max_id--
		while read line
		do
			title=`echo "$line" | awk 'BEGIN { FS="/" } {print $NF}'`
			rel_path=`echo "${line:${#MOVIE_DIR}+1:${#line}}"`
			grep "$rel_path" "$DATABASE" > /dev/null
			if [ $? -ne 0 ]
			then
				db_add "$title" "$rel_path"
			fi
		done < "$TEMP_DIR/list_fullpath"	
		echo "Database update complete"
	fi
}

# param = title, field
function db_get 
{
	if [ $# -ne 2 ]
	then
		return
	fi
	
	read firstline < "$DATABASE"
	fieldnum=`echo $firstline | awk -v awk_field=$2 -F, '{ for(i=1; i<=NF; i++) if( $i == awk_field ) print i }'`
	
	awk -v awk_title="$1" -v awk_fieldnum=$fieldnum -F, '{
		if( $6 == awk_title ) print $awk_fieldnum;
	}' "$DATABASE"
}

# param = rel_path
function db_remove 
{
	echo "Removing from database: $1"
	
	awk -v awk_rel="$1" -F, '{ if( $7 != awk_rel ) print $0 }' "$DATABASE" > "$TEMP_DIR/db_remove.csv"
	
	mv -f "$TEMP_DIR/db_remove.csv" "$DATABASE"
}

# param = external database path
function db_sync {
	echo "Syncing from external database"
	
	# initialize the temp db
	db_touch "$TEMP_DIR/db_sync.csv"
	
	while read line
	do
		title=`echo "$line" | cut -d"," -f6`
		ext_line=`grep "$title" "$1"`
		
		[ "$title" == "title" ] && continue # skip the first line

		# get the stats
		old_rating=`echo 	"$line" | cut -d"," -f2`
		old_playcount=`echo "$line" | cut -d"," -f3`
		old_actor=`echo 	"$line" | cut -d"," -f4`
		old_category=`echo 	"$line" | cut -d"," -f5`
		old_delete=`echo 	"$line" | cut -d"," -f8`
		old_split=`echo 	"$line" | cut -d"," -f9`
		rel_path=`echo 		"$line" | cut -d"," -f7`		
		
		new_rating=`echo 	"$ext_line" | cut -d"," -f2`
		new_playcount=`echo "$ext_line" | cut -d"," -f3`
		new_actor=`echo 	"$ext_line" | cut -d"," -f4`
		new_category=`echo 	"$ext_line" | cut -d"," -f5`
		new_delete=`echo 	"$ext_line" | cut -d"," -f8`
		new_split=`echo 	"$ext_line" | cut -d"," -f9`
		
		# updating index
		let index++
		newline="$index"
		
		if [ "$ext_line" == "" ]
		then
			newline="$newline","$old_rating","$old_playcount","$old_actor","$old_category","$title","$rel_path","$old_delete","$old_split"
		else
			echo "Updating $title"
			
			[ $new_rating -gt 0 ] && newline="$newline","$new_rating" || newline="$newline","$old_rating"
			
			let playcount=$new_playcount+$old_playcount
			newline="$newline","$playcount"

			[ "$new_actor" != "Unknown" ] && newline="$newline","$new_actor" || newline="$newline","$old_actor"
			[ "$new_category" != "Straight" ] && newline="$newline","$new_category" || newline="$newline","$old_category"
			
			newline="$newline","$title","$rel_path"
			
			[ $new_delete -gt 0 ] && newline="$newline","$new_delete" || newline="$newline","$old_delete"
			[ $new_split -gt 0 ] && newline="$newline","$new_split" || newline="$newline","$old_split"
		fi
		
		echo "$newline" >> "$TEMP_DIR/db_sync.csv"
		
	done < "$DATABASE"
	
	mv -f "$TEMP_DIR/db_sync.csv" "$DATABASE"
}

# param = (opt) file path
function db_touch 
{
	if [ $# -eq 0 ]
	then
		echo "index,rating,playcount,actor,category,title,rel_path,delete,split" > "$DATABASE"
	elif [ $# -eq 1 ]
	then
		echo "index,rating,playcount,actor,category,title,rel_path,delete,split" > "$1"
	else
		echo "**ERROR** Invalid number of parameters to $FUNCNAME"
	fi
}

# parameters are title, field=value, (opt)filepath
function db_update 
{
	if [ $# -eq 2 ]
	then
		dest="$DATABASE"
	elif [ $# -eq 3 ]
	then
		dest="$3"
	else
		echo "**ERROR** Wrong number of parameters passed to $FUNCNAME"
		return
	fi
	
	field=`echo "$2" | awk -F= '{ print $1; }'`
	value=`echo "$2" | awk -F= '{ print $2; }'`
	if [ -z "$value" ]
	then
		echo "**ERROR** Improper argument for $FUNCNAME"
		return
	else
		echo "Updating $field to $value for $1"
	fi
	
	read firstline < "$dest"
	fieldnum=`echo $firstline | awk -v awk_field=$field -F, '{ for(i=1; i<=NF; i++) if( $i == awk_field ) print i }'`
	
	awk -v awk_title="$1" -v awk_fieldnum=$fieldnum -v awk_value="$value" -F, '{
		if( $6 == awk_title )
		{
			for(i=1; i<awk_fieldnum; i++ ) printf "%s,", $i;
			printf "%s", awk_value;
			for(i=awk_fieldnum+1; i<=NF; i++ ) printf ",%s", $i;
			printf "\n";
		}
		else
			print $0
	}' "$dest" > "$TEMP_DIR/db_update.csv"
	
	mv -f "$TEMP_DIR/db_update.csv" "$dest"
}



