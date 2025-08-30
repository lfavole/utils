import datetime
import json
import os
import zoneinfo
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def make_request(bot_token: str, method: str, params: dict) -> Any:
    """
    Make a request to the Telegram API.

    Raises:
        RuntimeError: if the call to the Telegram API fails.
    """
    error = False
    try:
        with urlopen(
            Request(
                f"https://api.telegram.org/bot{bot_token}/{method}",
                json.dumps(params).encode(),
                {"Content-Type": "application/json"},
                method="POST",
            )
        ) as f:
            data = json.load(f)
    except HTTPError as e:
        error = e
        data = json.load(e.file)

    if not data["ok"] or error:
        msg = f"Failed to call Telegram API: {data['description']}"
        if error:
            new_error = RuntimeError(msg)
            new_error.data = data
            raise new_error from error
        raise RuntimeError(msg)

    return data["result"]


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> None:
    """
    Send a message to a Telegram chat.
    """
    return make_request(bot_token, "sendMessage", {"chat_id": chat_id, "text": message})


def delete_telegram_message(bot_token: str, chat_id: str, message_id: str) -> None:
    """
    Delete a message in a Telegram chat.
    """
    try:
        return make_request(bot_token, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except RuntimeError as e:
        if "message to delete not found" in e.data.get("description", ""):
            print("Previous message has been deleted, skipping deletion")
        else:
            raise


def get_review_data(identifier: str, is_email: bool) -> dict:
    """
    Check if the user has reviewed Duolingo based on the streak end date.
    """
    escaped_identifier = quote(identifier)
    url = f"https://duolingo.com/2017-06-30/users?{'email' if is_email else 'username'}={escaped_identifier}"

    with urlopen(url) as response:
        data = json.loads(response.read().decode())
        end_date_str = data["users"][0]["streakData"]["currentStreak"]["endDate"]
        end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()

        # Get the current date in Europe/Paris timezone
        paris_tz = zoneinfo.ZoneInfo("Europe/Paris")
        current_date = datetime.datetime.now(paris_tz).date()

        current_course_id = data["users"][0]["currentCourseId"]
        current_course_name = ""
        for course in data["users"][0]["courses"]:
            if course["id"] == current_course_id:
                current_course_name = course["title"]
                break

        return {
            "course_name": current_course_name,
            "has_reviewed": end_date >= current_date,
            "last_review_human_friendly": (
                "yesterday" if end_date == current_date - datetime.timedelta(days=1) else end_date_str
            ),
        }


# Main execution
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
USERNAME = os.getenv("DUOLINGO_USERNAME", "")
EMAIL = os.getenv("DUOLINGO_EMAIL", "")

if not USERNAME and not EMAIL:
    raise ValueError("Either DUOLINGO_USERNAME or DUOLINGO_EMAIL must be provided.")

# Determine if the identifier is an email or username
is_email = bool(EMAIL)
duolingo_identifier = EMAIL if is_email else USERNAME

MESSAGE_ID_FILE = Path(__file__).parent / ".duolingo_message_id"

if MESSAGE_ID_FILE.exists():
    message_id = MESSAGE_ID_FILE.read_text("utf-8").strip()
    if message_id:
        delete_telegram_message(BOT_TOKEN, CHAT_ID, message_id)

MESSAGE_ID_FILE.write_text("")

data = get_review_data(duolingo_identifier, is_email)

if not data["has_reviewed"]:
    message = (
        "You haven't reviewed "
        + (f"your {data['course_name']} lesson" if data["course_name"] else "Duolingo")
        + f" since {data['last_review_human_friendly']}. Please take a moment to do so."
    )
    print(message)
    result = send_telegram_message(BOT_TOKEN, CHAT_ID, message)
    MESSAGE_ID_FILE.write_text(str(result["message_id"]), "utf-8")
else:
    print("You have reviewed Duolingo recently.")
