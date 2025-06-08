# Timelapse cretor

This script:
* downloads videos from a FTP server
* creates a timelapse from these videos
* sends the timelapse with a Telegram bot
* renames the folder so it is not created twice
* backs up the timelapse to the FTP server

You will need to set the following environment variables:
* `AUDIO_FILES` (if needed, otherwise uses some videos from YouTube)
* `FTP_HOST`
* `FTP_PORT` (if needed, otherwise `21`)
* `FTP_USERNAME` (if needed, otherwise `freebox`)
* `FTP_PASSWORD`
* `FTP_PATH` (if needed, otherwise `/Disque dur/Camera`)
* `TELEGRAM_BOT_TOKEN`
* `TELEGRAM_CHAT_IDS`
