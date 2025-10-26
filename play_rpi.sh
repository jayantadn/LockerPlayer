#!/bin/bash

# LockerPlayer - Random Movie Player for Raspberry Pi 3B+
# Plays random movies from hardcoded configuration

# Hardcoded configuration values
MOVIE_DIR="./"
PLAYER="/usr/bin/vlc"
EXCEL_FILE="./LockerDB_mini.csv"

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
    
    # Get the movie path from the selected line
    REL_PATH=$(sed -n "${RANDOM_LINE}p" "$EXCEL_FILE" | cut -d',' -f1)
    
    # Construct full movie path
    SELECTED_MOVIE="${MOVIE_DIR}${REL_PATH}"
    
    echo "Selected movie: $REL_PATH"
    
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
        echo -n "Enter new movie rating (0-5, or 'c' to cancel): "
        read -r new_rating
        
        # Check if user wants to cancel
        if [ "$new_rating" = "c" ] || [ "$new_rating" = "C" ]; then
            echo "Rating cancelled."
            return 0
        fi
        
        # Validate numeric input
        if [[ "$new_rating" =~ ^[0-9]+$ ]] && [ "$new_rating" -ge 0 ] && [ "$new_rating" -le 5 ]; then
            break
        else
            echo "Invalid input. Please enter a number between 0-5, or 'c' to cancel."
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
    # TODO: Implement actor rating functionality
    echo "Rate actor functionality not yet implemented."
}

# Function to delete the movie
delete_movie() {
    # TODO: Implement movie deletion functionality
    echo "Delete movie functionality not yet implemented."
}

# Function to delete the actor
delete_actor() {
    # TODO: Implement actor deletion functionality
    echo "Delete actor functionality not yet implemented."
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
        echo "0. Exit"
        echo -n "Please select an option (1 or 0): "
        
        read -r choice
        
        case $choice in
            1)
                echo ""
                if select_random_movie; then
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
                echo "Invalid option. Please select 1 or 0."
                echo ""
                ;;
        esac
    done
}

# Main script execution
main() {
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
