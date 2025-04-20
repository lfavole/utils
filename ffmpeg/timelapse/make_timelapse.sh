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

echo "Starting the script..."

# If config.sh doesn't exist, raise an error
if [ ! -f config.sh ]; then
  echo "Error: config.sh not found. Please create it with your FTP credentials."
  exit 1
fi

# Load FTP credentials from config.sample.sh and config.sh
source config.sample.sh
source config.sh

# If some variables are not set, raise an error
required_vars=(FTP_USERNAME FTP_PASSWORD FTP_PATH AUDIO_FILES TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_IDS)
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "Error: $var is not set. Please set it in config.sh."
    exit 1
  fi
done

# If FTP_PATH is not a valid URL, raise an error
if ! [[ "$FTP_PATH" =~ ^ftp:// ]]; then
  echo "Error: FTP_PATH is not a valid URL. Please set it in config.sh."
  exit 1
fi

SCRIPT_DIR=$(dirname "$0")

date="${1:-"yesterday"}"

# Get the date in YYYYMMDD format
yyyymmdd=$(date -d "$date" +"%Y%m%d")
echo "Date: $yyyymmdd"

# Set the locale to French
export LC_TIME=fr_FR.UTF-8

# Get the French date
french_date=$(date -d "$date" +"%-d %B %Y")

# Check if the day is the 1st and needs the "er" suffix
day=$(date -d "$date" +"%-d")
if [ "$day" -eq 1 ]; then
  french_date="1er $(date -d "$date" +"%B %Y")"
fi
echo "Formatted date: $french_date"

#########################################
# 1. Copy the files from the FTP server #
#########################################

# Define source FTP directory and destination local directory
source_ftp="$FTP_PATH/$yyyymmdd"
destination_local="$TMP_DIR/$yyyymmdd"

FTP_SERVER=$(echo $FTP_PATH | awk -F'/' '{print $3}')
FTP_DIR=$(echo $FTP_PATH | awk -F'/' '{for (i=4; i<=NF; i++) printf "%s/", $i; print ""}' | sed 's:/$::')"/$yyyymmdd"

# If the source FTP directory doesn't exist, stop here
if ! tnftp -v -n "$FTP_SERVER" <<EOF | grep -q "250 "
quote USER "$FTP_USERNAME"
quote PASS "$FTP_PASSWORD"
cd "$FTP_DIR"
bye
EOF
then
  echo "Source FTP directory $source_ftp does not exist."
  exit
fi

# Create the destination directory if it doesn't exist
mkdir -p "$destination_local"
echo "Destination directory created: $destination_local"
echo

echo "Copying files from FTP server from $source_ftp to $destination_local..."

# Use wget to copy files from the FTP directory to the local directory
wget -q --show-progress -r --no-parent -nH --cut-dirs=3 --ftp-user="$FTP_USERNAME" --ftp-password="$FTP_PASSWORD" -A "*.mp4" "$source_ftp" -P "$destination_local"
echo "Files copied from $source_ftp to $destination_local"
echo

#############################################
# 2. Concatenate and speed up all the files #
#############################################

# Create a file list
filelist="$TMP_DIR/filelist.txt"
for f in "$destination_local"/*.mp4; do echo "file '$f'" >> "$filelist"; done
echo "File list created: $filelist"
echo

#########################################
# 3. Add the title and transition pages #
#########################################

font_path="$TMP_DIR/Montserrat-Black.ttf"
echo "Downloading Montserrat font into $font_path..."
wget -q --show-progress -O "$font_path" "https://raw.githubusercontent.com/JulietaUla/Montserrat/refs/heads/master/fonts/ttf/Montserrat-Black.ttf"
echo "Font downloaded: $font_path"
echo

# Concatenate the text page (without the last second) and the transition with the input video
output_video="$SCRIPT_DIR/$yyyymmdd.mp4"
echo "Concatenating everything into $output_video..."

# Initialize the ffmpeg command with input files
FFMPEG_CMD='ffmpeg -y -hide_banner -stats -safe 0 -f concat -i "$filelist" -i $(ls "$destination_local"/*.mp4 | head -n 1) -f lavfi -t 5 -i color=c=black:s=1280x720'

# Add audio files to the command
for FILE in "${AUDIO_FILES[@]}"
do
    FFMPEG_CMD+=" -i \"$(eval echo "$FILE")\""
done

# Build the filter_complex string
FILTER_COMPLEX="[0:v]setpts=PTS/10[spedup]; \
 \
 [2:v]drawtext=fontfile=$font_path:text='$french_date':fontcolor=white:fontsize=96:x=(w-text_w)/2:y=(h-text_h)/2[text]; \
 [text]split[text1][text2]; \
 [text1]format=rgba,fade=t=out:st=0:d=1:alpha=1[fade]; \
 [spedup][fade]overlay[transition]; \
 \
 [1:v]setpts=PTS/10,trim=start=1,setpts=PTS-STARTPTS[spedup_without_1s]; \
 [text2][transition][spedup_without_1s]concat=n=3:v=1:a=0[v];"

# Add audio concat filter
FILTER_COMPLEX_AUDIO=""
i=3
for ((j=0; j<${#AUDIO_FILES[@]}; j++))
do
    FILTER_COMPLEX_AUDIO+="[$i:a]"
    i=$((i + 1))
done
FILTER_COMPLEX_AUDIO+="concat=n=${#AUDIO_FILES[@]}:v=0:a=1[a]"

# Complete the filter_complex string
FILTER_COMPLEX+="$FILTER_COMPLEX_AUDIO"

# Complete the ffmpeg command
FFMPEG_CMD+=' -filter_complex "$FILTER_COMPLEX" -map "[v]" -map "[a]" -shortest -b:a 96k -b:v 1200k "$output_video"'

# Execute the ffmpeg command
eval "$FFMPEG_CMD"
echo "Final video created: $output_video"
echo

#################################
# 4. Send the video to Telegram #
#################################

# Send with a Telegram bot
echo "Sending video to Telegram..."
for chat_id in "${TELEGRAM_CHAT_IDS[@]}"; do
  curl --fail-with-body -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendVideo" \
    -F chat_id="$chat_id" \
    -F video=@"$output_video" \
    -F caption="Vidéo du $french_date" \
    -F parse_mode="HTML"
  if [ $? -ne 0 ]; then
    echo
    echo "Error: Failed to send video to Telegram."
    exit 1
  fi
  echo
  echo "Video sent to Telegram."
done

#############################################
# 5. Rename the directory on the FTP server #
#############################################

# Directories
OLD_DIR="$FTP_DIR"
NEW_DIR="${FTP_DIR}_ok"

# If the date is before today, stop here
# Compare the date with today
today=$(date +"%Y%m%d")
if [ "$yyyymmdd" -lt "$today" ]; then
  echo "Renaming $OLD_DIR directory to $NEW_DIR on FTP server..."

  # Use tnftp to rename the directory
  ENCODED_PASSWORD=$(echo "$FTP_PASSWORD" | python3 -c "import urllib.parse; print(urllib.parse.quote(input(), ''))")
  tnftp -v -n -i "ftp://$FTP_USERNAME:$ENCODED_PASSWORD@$FTP_SERVER/" <<EOF
rename "$OLD_DIR" "$NEW_DIR"
bye
EOF
  if [ $? -ne 0 ]; then
    echo "Error: Failed to rename directory on FTP server."
    exit 1
  fi
  echo "Directory renamed."
else
  echo "Date is today or future. Skipping directory rename."
fi

echo "Script completed."
