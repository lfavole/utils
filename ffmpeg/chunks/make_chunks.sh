#!/bin/bash

# Stop on every error
set -e  # Exit immediately if a command exits with a non-zero status
set -u  # Treat unset variables as an error when substituting

# Temporary directory with random name
TMP_DIR=$(mktemp -d)

# Function to clean up the temporary directory
function cleanup {
  rm -rf "$TMP_DIR"
  echo "Deleted temp working directory $TMP_DIR"
}

# Register the cleanup function to be called on the EXIT signal
trap cleanup EXIT

# Load default FTP credentials from config.sample.sh
source config.sample.sh

# Override default FTP credentials with custom credentials from config.sh
source config.sh

# Ensure FTP credentials are set
if [[ -z "$FTP_SERVER" || -z "$FTP_USERNAME" || -z "$FTP_PASSWORD" ]]; then
  echo "FTP credentials are not fully set. Please check config.sh."
  exit 1
fi

# Check if video file argument is provided
if [[ -z "$1" ]]; then
  echo "Usage: $0 <video_file_name>"
  exit 1
fi

REMOTE_VIDEO="$1"
LOCAL_VIDEO="$TMP_DIR/"$(basename "$REMOTE_VIDEO")
CHUNK_DURATION="00:05:00" # 5 minutes duration for each chunk

# Extract the basename (without extension) for directory creation
LOCAL_VIDEO_DIR="$TMP_DIR/chunks"
REMOTE_VIDEO_DIR="${REMOTE_VIDEO%.mp4}"

# Download the video file using tnftp
echo "Downloading $REMOTE_VIDEO from FTP server to $LOCAL_VIDEO..."
wget --ftp-user="$FTP_USERNAME" --ftp-password="$FTP_PASSWORD" -P "$TMP_DIR" "ftp://$FTP_SERVER/$REMOTE_VIDEO"

if [[ ! -f "$LOCAL_VIDEO" ]]; then
  echo "Failed to download $REMOTE_VIDEO"
  exit 1
fi

# Create a directory named after the video's basename
echo "Creating directory $LOCAL_VIDEO_DIR..."
mkdir -p "$LOCAL_VIDEO_DIR"

# Split the video into 5-minute chunks using ffmpeg
echo "Splitting $LOCAL_VIDEO into chunks..."
ffmpeg -i "$LOCAL_VIDEO" -c copy -map 0 -segment_time $CHUNK_DURATION -f segment -reset_timestamps 1 "$LOCAL_VIDEO_DIR/%03d.mp4"

# read -p "Press Enter to continue" </dev/tty

# Create a directory named after the video's basename
echo "Creating directory $REMOTE_VIDEO_DIR on FTP server and uploading chunks..."
ENCODED_PASSWORD=$(echo "$FTP_PASSWORD" | python3 -c "import urllib.parse; print(urllib.parse.quote(input(), ''))")
tnftp -i "ftp://$FTP_USERNAME:$ENCODED_PASSWORD@$FTP_SERVER/" <<EOF
mkdir "$REMOTE_VIDEO_DIR"
cd "$REMOTE_VIDEO_DIR"
lcd "$LOCAL_VIDEO_DIR"
mput *.mp4
bye
EOF

echo "Process completed successfully."
