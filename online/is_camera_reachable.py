"""
Check if the camera is reachable. If not, send a Telegram message.

If the weather is stormy, send the message only if the camera is reachable to unplug it.
"""
import json
import os
from base64 import b64encode
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from weather import is_storm


def is_host_reachable(url: str, username: str | None, password: str | None):
    try:
        headers = {}
        if username or password:
            headers["Authorization"] = "Basic " + b64encode((username + ":" + password).encode()).decode()
        # Send a request to the URL
        response = urlopen(Request(url, headers=headers), timeout=5)  # Set a timeout for the request
        # Check if the response status code is 200 (OK)
        if response.getcode() == 200:
            return True
        else:
            return False
    except HTTPError as e:
        print(f"HTTP error occurred: {e.code}")
        return False
    except URLError as e:
        print(f"URL error occurred: {e.reason}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def make_request(bot_token: str, method: str, params: dict) -> Any:  # noqa: ANN401
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

    Args:
        bot_token (str): Token of the Telegram bot.
        chat_id (str): ID of the Telegram chat.
        message (str): The message to send.

    """
    return make_request(bot_token, "sendMessage", {"chat_id": chat_id, "text": message})


def delete_telegram_message(bot_token: str, chat_id: str, message_id: str) -> None:
    """
    Delete a message in a Telegram chat.

    Args:
        bot_token (str): Token of the Telegram bot.
        chat_id (str): ID of the Telegram chat.
        message_id (str): The ID of the message to delete.

    Raises:
        RuntimeError: if the call to the Telegram API fails and the message to delete exists.

    """
    try:
        return make_request(bot_token, "deleteMessage", {"chat_id": chat_id, "message_id": message_id})
    except RuntimeError as e:
        if "message to delete not found" in e.data.get("description", ""):
            print("Previous message has been deleted, skipping deletion")
        else:
            raise


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

MESSAGE_ID_FILE = Path(__file__).parent / ".camera_message_id"

if MESSAGE_ID_FILE.exists():
    message_id = MESSAGE_ID_FILE.read_text("utf-8").strip()
    if message_id:
        delete_telegram_message(BOT_TOKEN, CHAT_ID, message_id)

MESSAGE_ID_FILE.write_text("")

message = []
no_send_message = []

OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
if OPENWEATHERMAP_API_KEY:
    try:
        LATITUDE = float(os.getenv("LATITUDE", ""))
        LONGITUDE = float(os.getenv("LONGITUDE", ""))
    except ValueError:
        LATITUDE = None
        LONGITUDE = None
    if any(item in (None, "") for item in (LATITUDE, LONGITUDE)):
        raise ValueError("LATITUDE or LONGITUDE is empty")

    try:
        storm = is_storm(LATITUDE, LONGITUDE, OPENWEATHERMAP_API_KEY)
    except HTTPError as e:
        message.append(
            "Erreur lors de la récupération de la météo :\n"
            f"{type(e).__name__}: {e}\n"
            "Veuillez corriger cette erreur."
        )
else:
    storm = False

CAMERA_URL = os.getenv("CAMERA_URL")
if not CAMERA_URL:
    raise ValueError("CAMERA_URL is empty")

CAMERA_USERNAME = os.getenv("CAMERA_USERNAME") or "admin"
CAMERA_PASSWORD = os.getenv("CAMERA_PASSWORD")

is_camera_reachable = is_host_reachable(CAMERA_URL, CAMERA_USERNAME, CAMERA_PASSWORD)

if not storm:
    if not is_camera_reachable:
        message.append(
            "La caméra n'est pas connectée. Veuillez vérifier si elle est correctement branchée "
            "et si le Wi-Fi est activé."
        )
    else:
        no_send_message.append("La caméra est connectée et il fait beau")
else:
    if is_camera_reachable:
        message.append("La caméra est connectée et le temps va être orageux. Veuillez la débrancher.")
    else:
        no_send_message.append("La caméra est déconnectée et le temps est orageux")

print("\n\n".join((*message, *no_send_message)))

if message:
    result = send_telegram_message(BOT_TOKEN, CHAT_ID, "\n\n".join(message))
    MESSAGE_ID_FILE.write_text(str(result["message_id"]), "utf-8")
