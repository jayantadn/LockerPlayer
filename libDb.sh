function db_touch # param = (opt) file path
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

function db_add # param = title, rel_path
{
	if [ $# -eq 0 ]
	then
		echo "Please provide an argument to $FUNCNAME"
		return
	else
		echo "Adding to database: $2"
	fi

	let max_id++
	
	echo "$max_id,0,0,Unknown,Straight,$1,$2,0,0" >> "$DATABASE"
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

function db_update # parameters are title, field=value, (opt)filepath
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

function db_get # param = title, field
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

function db_remove # param = rel_path
{
	echo "Removing from database: $1"
	
	awk -v awk_rel="$1" -F, '{ if( $7 != awk_rel ) print $0 }' "$DATABASE" > "$TEMP_DIR/db_remove.csv"
	
	mv -f "$TEMP_DIR/db_remove.csv" "$DATABASE"
}

