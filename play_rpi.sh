#!/bin/bash

# LockerPlayer - Random Movie Player for Raspberry Pi 3B+
# Plays random movies from hardcoded configuration

# Hardcoded configuration values
MOVIE_DIR="./"
PLAYER="/usr/bin/vlc"
EXCEL_FILE="./LockerDB_mini.csv"

SELECTED_MOVIE=""
SELECTED_LINE=""

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
    echo ""
    
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
                exit 0
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
    
    # Show menu
    show_menu
}

# Run the main function
main
