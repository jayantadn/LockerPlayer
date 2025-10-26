#!/bin/bash

# LockerPlayer - Random Movie Player for Raspberry Pi 3B+
# Plays random movies from hardcoded configuration

# Hardcoded configuration values
MOVIE_DIR="./"
PLAYER="/usr/bin/vlc"
EXCEL_FILE="./LockerDB_mini.csv"
ACTOR_STATS_FILE="./actor_stats.csv"

SELECTED_MOVIE=""
SELECTED_LINE=""

# Function to count unplayed vs total movies
count_unplayed_movies() {
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Count total movies (excluding header)
    TOTAL_MOVIES=$(tail -n +2 "$EXCEL_FILE" | wc -l)
    
    # Count movies with playcount = 0 (excluding header)
    UNPLAYED_COUNT=$(tail -n +2 "$EXCEL_FILE" | awk -F',' '$2 == 0 {count++} END {print count+0}')
    
    echo ""
    echo "Unplayed movies: $UNPLAYED_COUNT / $TOTAL_MOVIES"
    echo ""
    
    return 0
}

# Function to select a random movie from CSV
select_random_movie() {
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Count total lines (excluding header)
    TOTAL_LINES=$(tail -n +2 "$EXCEL_FILE" | wc -l)
    
    if [ "$TOTAL_LINES" -eq 0 ]; then
        echo "Error: No movie entries found in CSV file!"
        return 1
    fi
    
    # Select a random line number (excluding header)
    RANDOM_LINE=$((RANDOM % TOTAL_LINES + 2))
    
    # Store the selected line number for later use
    SELECTED_LINE=$RANDOM_LINE
    
    # Get the full line for the selected movie
    SELECTED_MOVIE_LINE=$(sed -n "${RANDOM_LINE}p" "$EXCEL_FILE")
    
    # Extract all fields from the CSV line
    REL_PATH=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f1)
    PLAYCOUNT=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f2)
    MOVIE_RATING=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f3)
    ACTOR=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f4)
    CATEGORY=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f5)
    STUDIO=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f6)
    
    # Get actor rating from actor_stats.csv
    if [ -f "$ACTOR_STATS_FILE" ]; then
        ACTOR_RATING=$(tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR" '$1 == actor {print $2; exit}')
        if [ -z "$ACTOR_RATING" ]; then
            ACTOR_RATING="0"  # Default if actor not found
        fi
    else
        ACTOR_RATING="0"  # Default if file doesn't exist
    fi
    
    # Construct full movie path
    SELECTED_MOVIE="${MOVIE_DIR}${REL_PATH}"
    
    echo "Selected movie: $REL_PATH"
    echo "  Actor: $ACTOR"
    echo "  Studio: $STUDIO"
    echo "  Category: $CATEGORY"
    echo "  Play Count: $PLAYCOUNT"
    echo "  Movie Rating: $MOVIE_RATING"
    echo "  Actor Rating: $ACTOR_RATING"
    echo ""
    
    # Ask user what to do with the selected movie
    while true; do
        echo "What would you like to do?"
        echo "1. Play this movie"
        echo "2. Select another random movie"
        echo "0. Return to main menu"
        echo -n "Please select an option (0-2): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                return 0  # Proceed to play the movie
                ;;
            2)
                echo ""
                echo "Selecting another random movie..."
                echo ""
                # Recursively call select_random_movie to pick a new one
                select_random_movie
                return $?
                ;;
            0)
                echo ""
                echo "Returning to main menu..."
                return 1  # Return to main menu without playing
                ;;
            *)
                echo ""
                echo "Invalid option. Please select 0-2."
                ;;
        esac
    done
    
    return 0
}

# Function to select a random high-rated movie from CSV (rating >= 5)
select_high_rated_movie() {
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Create temporary file with high-rated movies (rating >= 5)
    TEMP_HIGH_RATED=$(mktemp)
    tail -n +2 "$EXCEL_FILE" | awk -F',' '$3 >= 5' > "$TEMP_HIGH_RATED"
    
    # Count high-rated movies
    HIGH_RATED_COUNT=$(wc -l < "$TEMP_HIGH_RATED")
    
    if [ "$HIGH_RATED_COUNT" -eq 0 ]; then
        echo "No high-rated movies (rating >= 5) found in database!"
        rm "$TEMP_HIGH_RATED"
        return 1
    fi
    
    echo "Found $HIGH_RATED_COUNT high-rated movies (rating >= 5)"
    echo ""
    
    # Select a random line from high-rated movies
    RANDOM_HIGH_RATED_LINE=$((RANDOM % HIGH_RATED_COUNT + 1))
    
    # Get the selected high-rated movie line
    SELECTED_MOVIE_LINE=$(sed -n "${RANDOM_HIGH_RATED_LINE}p" "$TEMP_HIGH_RATED")
    
    # Find the corresponding line number in the original CSV file
    REL_PATH_SEARCH=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f1)
    SELECTED_LINE=$(tail -n +2 "$EXCEL_FILE" | grep -n "^$REL_PATH_SEARCH," | cut -d':' -f1)
    SELECTED_LINE=$((SELECTED_LINE + 1))  # Adjust for header line
    
    # Clean up temporary file
    rm "$TEMP_HIGH_RATED"
    
    # Extract all fields from the CSV line
    REL_PATH=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f1)
    PLAYCOUNT=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f2)
    MOVIE_RATING=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f3)
    ACTOR=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f4)
    CATEGORY=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f5)
    STUDIO=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f6)
    
    # Get actor rating from actor_stats.csv
    if [ -f "$ACTOR_STATS_FILE" ]; then
        ACTOR_RATING=$(tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR" '$1 == actor {print $2; exit}')
        if [ -z "$ACTOR_RATING" ]; then
            ACTOR_RATING="0"  # Default if actor not found
        fi
    else
        ACTOR_RATING="0"  # Default if file doesn't exist
    fi
    
    # Construct full movie path
    SELECTED_MOVIE="${MOVIE_DIR}${REL_PATH}"
    
    echo "Selected high-rated movie: $REL_PATH"
    echo "  Actor: $ACTOR"
    echo "  Studio: $STUDIO"
    echo "  Category: $CATEGORY"
    echo "  Play Count: $PLAYCOUNT"
    echo "  Movie Rating: $MOVIE_RATING"
    echo "  Actor Rating: $ACTOR_RATING"
    echo ""
    
    # Ask user what to do with the selected movie
    while true; do
        echo "What would you like to do?"
        echo "1. Play this movie"
        echo "2. Select another high-rated movie"
        echo "0. Return to main menu"
        echo -n "Please select an option (0-2): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                return 0  # Proceed to play the movie
                ;;
            2)
                echo ""
                echo "Selecting another high-rated movie..."
                echo ""
                # Recursively call select_high_rated_movie to pick a new one
                select_high_rated_movie
                return $?
                ;;
            0)
                echo ""
                echo "Returning to main menu..."
                return 1  # Return to main menu without playing
                ;;
            *)
                echo ""
                echo "Invalid option. Please select 0-2."
                ;;
        esac
    done
    
    return 0
}

# Function to select a random unplayed movie from CSV (playcount = 0)
select_unplayed_movie() {
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Create temporary file with unplayed movies (playcount = 0)
    TEMP_UNPLAYED=$(mktemp)
    tail -n +2 "$EXCEL_FILE" | awk -F',' '$2 == 0' > "$TEMP_UNPLAYED"
    
    # Count unplayed movies
    UNPLAYED_COUNT=$(wc -l < "$TEMP_UNPLAYED")
    
    if [ "$UNPLAYED_COUNT" -eq 0 ]; then
        echo "No unplayed movies (playcount = 0) found in database!"
        rm "$TEMP_UNPLAYED"
        return 1
    fi
    
    echo "Found $UNPLAYED_COUNT unplayed movies (playcount = 0)"
    echo ""
    
    # Select a random line from unplayed movies
    RANDOM_UNPLAYED_LINE=$((RANDOM % UNPLAYED_COUNT + 1))
    
    # Get the selected unplayed movie line
    SELECTED_MOVIE_LINE=$(sed -n "${RANDOM_UNPLAYED_LINE}p" "$TEMP_UNPLAYED")
    
    # Find the corresponding line number in the original CSV file
    REL_PATH_SEARCH=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f1)
    SELECTED_LINE=$(tail -n +2 "$EXCEL_FILE" | grep -n "^$REL_PATH_SEARCH," | cut -d':' -f1)
    SELECTED_LINE=$((SELECTED_LINE + 1))  # Adjust for header line
    
    # Clean up temporary file
    rm "$TEMP_UNPLAYED"
    
    # Extract all fields from the CSV line
    REL_PATH=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f1)
    PLAYCOUNT=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f2)
    MOVIE_RATING=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f3)
    ACTOR=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f4)
    CATEGORY=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f5)
    STUDIO=$(echo "$SELECTED_MOVIE_LINE" | cut -d',' -f6)
    
    # Get actor rating from actor_stats.csv
    if [ -f "$ACTOR_STATS_FILE" ]; then
        ACTOR_RATING=$(tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR" '$1 == actor {print $2; exit}')
        if [ -z "$ACTOR_RATING" ]; then
            ACTOR_RATING="0"  # Default if actor not found
        fi
    else
        ACTOR_RATING="0"  # Default if file doesn't exist
    fi
    
    # Construct full movie path
    SELECTED_MOVIE="${MOVIE_DIR}${REL_PATH}"
    
    echo "Selected unplayed movie: $REL_PATH"
    echo "  Actor: $ACTOR"
    echo "  Studio: $STUDIO"
    echo "  Category: $CATEGORY"
    echo "  Play Count: $PLAYCOUNT"
    echo "  Movie Rating: $MOVIE_RATING"
    echo "  Actor Rating: $ACTOR_RATING"
    echo ""
    
    # Ask user what to do with the selected movie
    while true; do
        echo "What would you like to do?"
        echo "1. Play this movie"
        echo "2. Select another unplayed movie"
        echo "0. Return to main menu"
        echo -n "Please select an option (0-2): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                return 0  # Proceed to play the movie
                ;;
            2)
                echo ""
                echo "Selecting another unplayed movie..."
                echo ""
                # Recursively call select_unplayed_movie to pick a new one
                select_unplayed_movie
                return $?
                ;;
            0)
                echo ""
                echo "Returning to main menu..."
                return 1  # Return to main menu without playing
                ;;
            *)
                echo ""
                echo "Invalid option. Please select 0-2."
                ;;
        esac
    done
    
    return 0
}

# Function to increment playcount for the selected movie
increment_playcount() {
    if [ -z "$SELECTED_LINE" ]; then
        echo "Error: No movie line selected for playcount update!"
        return 1
    fi
    
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found for playcount update!"
        return 1
    fi
    
    # Create a temporary file
    TEMP_FILE=$(mktemp)
    
    # Read the current line and extract the playcount
    CURRENT_LINE=$(sed -n "${SELECTED_LINE}p" "$EXCEL_FILE")
    CURRENT_PLAYCOUNT=$(echo "$CURRENT_LINE" | cut -d',' -f2)
    
    # Increment the playcount
    NEW_PLAYCOUNT=$((CURRENT_PLAYCOUNT + 1))
    
    # Replace the playcount in the line
    NEW_LINE=$(echo "$CURRENT_LINE" | sed "s/,${CURRENT_PLAYCOUNT},/,${NEW_PLAYCOUNT},/")
    
    # Create new CSV with updated playcount
    {
        # Copy header and lines before the selected line
        sed -n "1,$((SELECTED_LINE-1))p" "$EXCEL_FILE"
        # Add the updated line
        echo "$NEW_LINE"
        # Copy lines after the selected line
        sed -n "$((SELECTED_LINE+1)),\$p" "$EXCEL_FILE"
    } > "$TEMP_FILE"
    
    # Replace the original file with the updated one
    mv "$TEMP_FILE" "$EXCEL_FILE"
    
    echo "Updated playcount to $NEW_PLAYCOUNT for selected movie."
    
    return 0
}

# Function to rate the movie
rate_movie() {
    if [ -z "$SELECTED_LINE" ]; then
        echo "Error: No movie selected for rating!"
        return 1
    fi
    
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Get current movie info
    CURRENT_LINE=$(sed -n "${SELECTED_LINE}p" "$EXCEL_FILE")
    CURRENT_MOVIE_PATH=$(echo "$CURRENT_LINE" | cut -d',' -f1)
    CURRENT_MOVIE_RATING=$(echo "$CURRENT_LINE" | cut -d',' -f3)
    
    echo "Current movie: $CURRENT_MOVIE_PATH"
    echo "Current movie rating: $CURRENT_MOVIE_RATING"
    echo ""
    
    while true; do
        echo -n "Enter new movie rating (0-6, or 'c' to cancel): "
        read -r new_rating
        
        # Check if user wants to cancel
        if [ "$new_rating" = "c" ] || [ "$new_rating" = "C" ]; then
            echo "Rating cancelled."
            return 0
        fi
        
        # Validate numeric input
        if [[ "$new_rating" =~ ^[0-9]+$ ]] && [ "$new_rating" -ge 0 ] && [ "$new_rating" -le 6 ]; then
            break
        else
            echo "Invalid input. Please enter a number between 0-6, or 'c' to cancel."
        fi
    done
    
    # Create a temporary file
    TEMP_FILE=$(mktemp)
    
    # Replace the movie rating in the line (3rd field)
    NEW_LINE=$(echo "$CURRENT_LINE" | awk -F',' -v rating="$new_rating" 'BEGIN{OFS=","} {$3=rating; print}')
    
    # Create new CSV with updated movie rating
    {
        # Copy header and lines before the selected line
        sed -n "1,$((SELECTED_LINE-1))p" "$EXCEL_FILE"
        # Add the updated line
        echo "$NEW_LINE"
        # Copy lines after the selected line
        sed -n "$((SELECTED_LINE+1)),\$p" "$EXCEL_FILE"
    } > "$TEMP_FILE"
    
    # Replace the original file with the updated one
    mv "$TEMP_FILE" "$EXCEL_FILE"
    
    echo "Movie rating updated from $CURRENT_MOVIE_RATING to $new_rating."
}

# Function to rate the actor
rate_actor() {
    if [ -z "$SELECTED_LINE" ]; then
        echo "Error: No movie selected for actor rating!"
        return 1
    fi
    
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    if [ ! -f "$ACTOR_STATS_FILE" ]; then
        echo "Error: Actor stats file $ACTOR_STATS_FILE not found!"
        return 1
    fi
    
    # Get current movie info to extract actor name
    CURRENT_LINE=$(sed -n "${SELECTED_LINE}p" "$EXCEL_FILE")
    ACTOR_NAME=$(echo "$CURRENT_LINE" | cut -d',' -f4)
    
    # Get current actor rating from actor_stats.csv
    CURRENT_ACTOR_RATING=$(tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR_NAME" '$1 == actor {print $2; exit}')
    if [ -z "$CURRENT_ACTOR_RATING" ]; then
        CURRENT_ACTOR_RATING="0"
    fi
    
    echo "Current actor: $ACTOR_NAME"
    echo "Current actor rating: $CURRENT_ACTOR_RATING"
    echo ""
    
    while true; do
        echo -n "Enter new actor rating (0-6, or 'c' to cancel): "
        read -r new_rating
        
        # Check if user wants to cancel
        if [ "$new_rating" = "c" ] || [ "$new_rating" = "C" ]; then
            echo "Actor rating cancelled."
            return 0
        fi
        
        # Validate numeric input
        if [[ "$new_rating" =~ ^[0-9]+$ ]] && [ "$new_rating" -ge 0 ] && [ "$new_rating" -le 6 ]; then
            break
        else
            echo "Invalid input. Please enter a number between 0-6, or 'c' to cancel."
        fi
    done
    
    # Create a temporary file for actor stats
    TEMP_FILE=$(mktemp)
    
    # Check if actor exists in actor_stats.csv
    ACTOR_LINE_NUM=$(tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR_NAME" '$1 == actor {print NR+1; exit}')
    
    if [ -n "$ACTOR_LINE_NUM" ]; then
        # Update existing actor rating
        ACTOR_CURRENT_LINE=$(sed -n "${ACTOR_LINE_NUM}p" "$ACTOR_STATS_FILE")
        NEW_ACTOR_LINE=$(echo "$ACTOR_CURRENT_LINE" | awk -F',' -v rating="$new_rating" 'BEGIN{OFS=","} {$2=rating; print}')
        
        # Create new actor stats file with updated rating
        {
            # Copy header and lines before the actor line
            sed -n "1,$((ACTOR_LINE_NUM-1))p" "$ACTOR_STATS_FILE"
            # Add the updated line
            echo "$NEW_ACTOR_LINE"
            # Copy lines after the actor line
            sed -n "$((ACTOR_LINE_NUM+1)),\$p" "$ACTOR_STATS_FILE"
        } > "$TEMP_FILE"
    else
        # Add new actor entry
        {
            # Copy existing file
            cat "$ACTOR_STATS_FILE"
            # Add new actor line
            echo "$ACTOR_NAME,$new_rating,"
        } > "$TEMP_FILE"
    fi
    
    # Replace the original file with the updated one
    mv "$TEMP_FILE" "$ACTOR_STATS_FILE"
    
    echo "Actor rating updated from $CURRENT_ACTOR_RATING to $new_rating for $ACTOR_NAME."
}

# Function to delete the movie
delete_movie() {
    if [ -z "$SELECTED_LINE" ]; then
        echo "Error: No movie selected for deletion!"
        return 1
    fi
    
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Get current movie info
    CURRENT_LINE=$(sed -n "${SELECTED_LINE}p" "$EXCEL_FILE")
    CURRENT_MOVIE_PATH=$(echo "$CURRENT_LINE" | cut -d',' -f1)
    
    echo "Movie to delete: $CURRENT_MOVIE_PATH"
    echo ""
    
    # Confirm deletion
    while true; do
        echo -n "Are you sure you want to delete this movie? (y/n): "
        read -r confirm
        
        case $confirm in
            [Yy]*)
                break
                ;;
            [Nn]*)
                echo "Deletion cancelled."
                return 0
                ;;
            *)
                echo "Please enter 'y' for yes or 'n' for no."
                ;;
        esac
    done
    
    # Create/append to to_delete.txt
    echo "movie=$CURRENT_MOVIE_PATH" >> "./to_delete.txt"
    echo "Added deletion record to to_delete.txt"
    
    # Delete the physical file
    FULL_MOVIE_PATH="${MOVIE_DIR}${CURRENT_MOVIE_PATH}"
    if [ -f "$FULL_MOVIE_PATH" ]; then
        rm "$FULL_MOVIE_PATH"
        echo "Deleted physical file: $FULL_MOVIE_PATH"
    else
        echo "Warning: Physical file not found: $FULL_MOVIE_PATH"
    fi
    
    # Update CSV file by removing the line
    TEMP_FILE=$(mktemp)
    
    # Create new CSV without the deleted movie line
    {
        # Copy header and lines before the selected line
        sed -n "1,$((SELECTED_LINE-1))p" "$EXCEL_FILE"
        # Skip the selected line (don't copy it)
        # Copy lines after the selected line
        sed -n "$((SELECTED_LINE+1)),\$p" "$EXCEL_FILE"
    } > "$TEMP_FILE"
    
    # Replace the original file with the updated one
    mv "$TEMP_FILE" "$EXCEL_FILE"
    
    echo "Movie removed from database."
    echo "Deletion completed successfully."
}

# Function to delete the actor
delete_actor() {
    if [ -z "$SELECTED_LINE" ]; then
        echo "Error: No movie selected for actor deletion!"
        return 1
    fi
    
    if [ ! -f "$EXCEL_FILE" ]; then
        echo "Error: CSV file $EXCEL_FILE not found!"
        return 1
    fi
    
    # Get current movie info to extract actor name
    CURRENT_LINE=$(sed -n "${SELECTED_LINE}p" "$EXCEL_FILE")
    ACTOR_NAME=$(echo "$CURRENT_LINE" | cut -d',' -f4)
    
    echo "Actor: $ACTOR_NAME"
    echo ""
    
    # Confirm deletion
    while true; do
        echo -n "Are you sure you want to delete ALL movies for actor '$ACTOR_NAME'? (y/n): "
        read -r confirm
        
        case $confirm in
            [Yy]*)
                break
                ;;
            [Nn]*)
                echo "Actor deletion cancelled."
                return 0
                ;;
            *)
                echo "Please enter 'y' for yes or 'n' for no."
                ;;
        esac
    done
    
    # Log actor deletion to to_delete.txt
    echo "actor=$ACTOR_NAME" >> "./to_delete.txt"
    echo "Added actor deletion record to to_delete.txt"
    
    # Get all movie paths for this actor and delete physical files
    DELETED_COUNT=0
    while IFS=',' read -r rel_path playcount movie_rating actor category studio; do
        if [ "$actor" = "$ACTOR_NAME" ]; then
            FULL_MOVIE_PATH="${MOVIE_DIR}${rel_path}"
            if [ -f "$FULL_MOVIE_PATH" ]; then
                rm "$FULL_MOVIE_PATH"
                echo "Deleted: $rel_path"
                DELETED_COUNT=$((DELETED_COUNT + 1))
            else
                echo "Warning: File not found: $rel_path"
            fi
        fi
    done < <(tail -n +2 "$EXCEL_FILE")
    
    # Update CSV file by removing all lines for this actor
    TEMP_FILE=$(mktemp)
    
    # Keep header and all lines except those with the specified actor
    {
        # Copy header
        head -n 1 "$EXCEL_FILE"
        # Copy all lines except those with the specified actor
        tail -n +2 "$EXCEL_FILE" | awk -F',' -v actor="$ACTOR_NAME" '$4 != actor'
    } > "$TEMP_FILE"
    
    # Replace the original file with the updated one
    mv "$TEMP_FILE" "$EXCEL_FILE"
    
    # Also remove actor from actor_stats.csv if it exists
    if [ -f "$ACTOR_STATS_FILE" ]; then
        ACTOR_TEMP_FILE=$(mktemp)
        {
            # Copy header
            head -n 1 "$ACTOR_STATS_FILE"
            # Copy all lines except the specified actor
            tail -n +2 "$ACTOR_STATS_FILE" | awk -F',' -v actor="$ACTOR_NAME" '$1 != actor'
        } > "$ACTOR_TEMP_FILE"
        
        # Replace the original file with the updated one
        mv "$ACTOR_TEMP_FILE" "$ACTOR_STATS_FILE"
        echo "Removed actor from actor_stats.csv: $ACTOR_NAME"
    fi
    
    echo "Deleted $DELETED_COUNT physical files."
    echo "Removed all database entries for actor: $ACTOR_NAME"
    echo "Actor deletion completed successfully."
}

# Function to show post-play menu
show_post_play_menu() {
    while true; do
        echo ""
        echo "=== Post-Play Options ==="
        echo "1. Rate movie"
        echo "2. Rate actor"
        echo "3. Delete movie"
        echo "4. Delete actor"
        echo "0. Return to main menu"
        echo -n "Please select an option (0-4): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                rate_movie
                ;;
            2)
                echo ""
                rate_actor
                ;;
            3)
                echo ""
                delete_movie
                ;;
            4)
                echo ""
                delete_actor
                ;;
            0)
                echo ""
                echo "Returning to main menu..."
                return 0
                ;;
            *)
                echo ""
                echo "Invalid option. Please select 0-4."
                ;;
        esac
    done
}

# Function to play the selected movie
play_movie() {
    if [ -z "$SELECTED_MOVIE" ]; then
        echo "Error: No movie selected!"
        return 1
    fi
    
    if [ ! -f "$SELECTED_MOVIE" ]; then
        echo "Warning: Movie file does not exist: $SELECTED_MOVIE"
        echo "Do you want to continue anyway? (y/n): "
        read -r continue_anyway
        if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
            return 1
        fi
    fi
    
    # Start the movie player with fullscreen parameters for VLC
    if [[ "$PLAYER" == *"vlc"* ]]; then
        "$PLAYER" --fullscreen --play-and-exit "$SELECTED_MOVIE" >/dev/null 2>&1
    else
        "$PLAYER" "$SELECTED_MOVIE"
    fi
    
    echo ""
    echo "Playback finished."
    
    # Increment playcount after successful playback
    increment_playcount
    
    # Show post-play menu
    show_post_play_menu
}

# Function to show menu and handle user input
show_menu() {
    while true; do

        echo "1. Play random movie"
        echo "2. Play high rated movie"
        echo "3. Play unplayed movie"
        echo "0. Exit"
        echo -n "Please select an option (0-3): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                if select_random_movie; then
                    play_movie
                fi
                echo ""
                ;;
            2)
                echo ""
                if select_high_rated_movie; then
                    play_movie
                fi
                echo ""
                ;;
            3)
                echo ""
                if select_unplayed_movie; then
                    play_movie
                fi
                echo ""
                ;;
            0)
                echo ""
                echo "Exiting LockerPlayer. Goodbye!"
                return 0
                ;;
            *)
                echo ""
                echo "Invalid option. Please select 0-3."
                echo ""
                ;;
        esac
    done
}

# Main script execution
main() {
    # Clear the screen at startup
    clear
    
    # Check if player exists
    if [ ! -f "$PLAYER" ]; then
        echo "Warning: Player $PLAYER not found!"
        echo "Please check your configuration."
        echo ""
    fi
    
    # Display number of unplayed movies
    count_unplayed_movies
    
    # Show menu
    show_menu
}

# Run the main function
main
