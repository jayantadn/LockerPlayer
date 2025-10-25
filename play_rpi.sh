#!/bin/bash

# LockerPlayer - Random Movie Player for Raspberry Pi 3B+
# Reads config and CSV to play random movies

CONFIG_FILE="config.ini"
SELECTED_MOVIE=""
MOVIE_DIR=""
PLAYER=""
EXCEL_FILE=""

# Function to read config file parameters
read_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Error: Config file $CONFIG_FILE not found!"
        exit 1
    fi
    
    # Read MOVIEDIR, PLAYER, and EXCEL from config.ini
    MOVIE_DIR=$(grep "^MOVIEDIR=" "$CONFIG_FILE" | cut -d'=' -f2)
    PLAYER=$(grep "^PLAYER=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '"')
    EXCEL_FILE=$(grep "^EXCEL=" "$CONFIG_FILE" | cut -d'=' -f2)
    
    # Remove any trailing slashes from MOVIE_DIR and add one
    MOVIE_DIR=$(echo "$MOVIE_DIR" | sed 's:/*$:/:')
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
    
    # Get the movie path from the selected line
    REL_PATH=$(sed -n "${RANDOM_LINE}p" "$EXCEL_FILE" | cut -d',' -f1)
    
    # Construct full movie path
    SELECTED_MOVIE="${MOVIE_DIR}${REL_PATH}"
    
    echo "Selected movie: $REL_PATH"
    echo "Full path: $SELECTED_MOVIE"
    echo ""
    
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
    
    echo "Playing movie: $SELECTED_MOVIE"
    echo "Using player: $PLAYER"
    echo ""
    echo "Starting playback..."
    
    # Start the movie player with fullscreen parameters for VLC
    if [[ "$PLAYER" == *"vlc"* ]]; then
        "$PLAYER" --fullscreen --play-and-exit "$SELECTED_MOVIE" >/dev/null 2>&1
    else
        "$PLAYER" "$SELECTED_MOVIE"
    fi
    
    echo ""
    echo "Playback finished."
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
                echo "Selecting random movie..."
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
    # Read configuration
    read_config
    
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
