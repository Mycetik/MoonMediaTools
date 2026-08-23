#!/bin/bash

DISPLAYNAME="MoonMediaTools"
NAME="mmt"
PAUSE="0"

cd "$(dirname "$0")"
APP_DIR="$(pwd)"
PROGRAM_DIR="$APP_DIR"

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/$NAME"
BIN_DIR="$DATA_DIR/bin"
PY_DIR="$DATA_DIR/python"

if [ "$EUID" -eq 0 ]; then

    if [ -n "$SUDO_USER" ]; then
        TARGET_USER="$SUDO_USER"
    else
        TARGET_USER=$(id -nu 1000)
    fi

    exec sudo -u "$TARGET_USER" "$0" "$@"
    
    exit 1 
fi

LOCK_FILE="/tmp/${NAME}.lock"
exec 9>"$LOCK_FILE"
flock -n 9 || {
    echo "The program has already been launched"
    exit 1
}

if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo "This program requires graphics"
    exit 1
fi

show_ok_window() {
    local message="${1:-OK}"
    if command -v zenity &> /dev/null; then
        zenity --info --text="$message" --title="$DISPLAYNAME"
    elif command -v kdialog &> /dev/null; then
        kdialog --msgbox "$message" --title "$DISPLAYNAME"
    elif command -v xmessage &> /dev/null; then
        xmessage -buttons OK -default OK -center "$message"
    else
        echo "Window error"
    fi
}

show_error_window() {
    local message="${1:-Unknown Error}"
    if command -v zenity &> /dev/null; then
        zenity --error --text="$message" --title="$DISPLAYNAME - Error"
    elif command -v kdialog &> /dev/null; then
        kdialog --error "$message" --title "$DISPLAYNAME - Error"
    elif command -v xmessage &> /dev/null; then
        xmessage -buttons OK -default OK -center "ERROR: $message"
    else
        echo "Window error"
    fi
}

LOADING_PID=""

show_loading_window() {
    local message="${1:-Please wait, the program is starting...}"
    if command -v zenity &> /dev/null; then
        zenity --info --text="$message" --title="$DISPLAYNAME" &
        LOADING_PID=$!
    elif command -v kdialog &> /dev/null; then
        kdialog --msgbox "$message" --title "$DISPLAYNAME" &
        LOADING_PID=$!
    elif command -v xmessage &> /dev/null; then
        xmessage -buttons OK -center "$message" &
        LOADING_PID=$!
    fi
}

close_loading_window() {
    if [ -n "$LOADING_PID" ] && kill -0 "$LOADING_PID" 2>/dev/null; then
        kill "$LOADING_PID" 2>/dev/null
    fi
}

fatal() {
    local text="${1:-Code 1}"
    
    echo "!PROGRAM PANIC!"
    echo "A critical error occurred in the program."
    echo "$text"

    show_error_window "The program encountered a critical error:\n\n$text"
}

echo "Program started"

show_loading_window "Please wait, checking dependencies and starting..."

mkdir -p "$BIN_DIR"
mkdir -p "$PY_DIR"

FREE_SPACE_KB=$(df -k "$DATA_DIR" | awk 'NR==2 {print $4}')
REQUIRED_KB=1048576

if [ "$FREE_SPACE_KB" -lt "$REQUIRED_KB" ]; then
    show_error_window "Launching the program when disk space is insufficient is dangerous. Launch cancelled"
    exit 1
fi

SETUP_MARKER="$DATA_DIR/.setup_completed"

if [ ! -f "$SETUP_MARKER" ]; then
    echo "Downloading components..."
    
    echo "Downloading FFmpeg..."
    FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
    curl -L "$FFMPEG_URL" | tar -xJ --strip-components=1 -C "$BIN_DIR" --wildcards '*/ffmpeg' '*/ffprobe'
    chmod +x "$BIN_DIR/ffmpeg" "$BIN_DIR/ffprobe"

    echo "Downloading Python 3.12..."
    PYTHON_URL="https://github.com/astral-sh/python-build-standalone/releases/download/20240415/cpython-3.12.3+20240415-x86_64-unknown-linux-gnu-install_only.tar.gz"
    curl -L "$PYTHON_URL" | tar -xz --strip-components=1 -C "$PY_DIR"

    export PATH="$BIN_DIR:$PY_DIR/bin:$PATH"
    export PYTHON_EXEC="python3"

    echo "Downloading Deno"
    DENO_URL="https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip"
    curl -L "$DENO_URL" -o "$BIN_DIR/deno.zip"
    $PYTHON_EXEC -c "import zipfile; zipfile.ZipFile('$BIN_DIR/deno.zip', 'r').extractall('$BIN_DIR')"
    rm "$BIN_DIR/deno.zip"
    chmod +x "$BIN_DIR/deno"

    touch "$SETUP_MARKER"
    echo "Setup successfully completed"
else
    export PATH="$BIN_DIR:$PY_DIR/bin:$PATH"
    export PYTHON_EXEC="python3"
fi

if [ ! -f "$BIN_DIR/yt-dlp-nightly" ]; then
    echo "Downloading yt-dlp nightly build..."
    NIGHTLY_URL="https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp_linux"
    curl -L "$NIGHTLY_URL" -o "$BIN_DIR/yt-dlp-nightly"
    chmod +x "$BIN_DIR/yt-dlp-nightly"
else
    "$BIN_DIR/yt-dlp-nightly" --update-to nightly > /dev/null 2>&1
fi

if [ -f /etc/NIXOS ] || [ -f /etc/NIXOS_RELEASE ]; then
    if ! command -v nix-ld >/dev/null 2>&1 && [ -z "$NIX_LD" ]; then
        echo "NixOS detected. Install nix-ld"
    fi
fi

close_loading_window
export XLIB_SKIP_ARGB_VISUALS=1
$PYTHON_EXEC $PROGRAM_DIR/main.py
PYTHON_EXIT_CODE=$?

if [ $PYTHON_EXIT_CODE -eq 0 ]; then
    FINAL_CODE=0

elif [ $PYTHON_EXIT_CODE -eq 10 ]; then
    FINAL_CODE=1

elif [ $PYTHON_EXIT_CODE -eq 13 ]; then
    FINAL_CODE=1

elif [ $PYTHON_EXIT_CODE -eq 139 ]; then
    fatal "Segmentation Fault (SIGSEGV 139)"
    FINAL_CODE=139

elif [ $PYTHON_EXIT_CODE -eq 134 ]; then
    fatal "Aborted (SIGABRT 134)"
    FINAL_CODE=134

else
    fatal "Process exited with code: $PYTHON_EXIT_CODE"
    FINAL_CODE=$PYTHON_EXIT_CODE
fi

echo ""
if [ "$PAUSE" = "1" ]; then
    echo "Press any key to continue..."
    read -n 1 -s -r
    echo ""
fi

exit $FINAL_CODE