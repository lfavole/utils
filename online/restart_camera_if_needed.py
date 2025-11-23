"""Restart the camera if there is an error in its logs."""
import base64
import os
import random
import re
import socket
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

socket.setdefaulttimeout(10)

CAMERA_URL = os.getenv("CAMERA_URL", "")
CAMERA_USERNAME = os.getenv("CAMERA_USERNAME", "") or "admin"
CAMERA_PASSWORD = os.getenv("CAMERA_PASSWORD", "")

if not CAMERA_URL:
    raise ValueError("CAMERA_URL is empty")
if not CAMERA_PASSWORD:
    raise ValueError("CAMERA_PASSWORD is empty")

auth_header = {"Authorization": "Basic " + base64.b64encode(f"{CAMERA_USERNAME}:{CAMERA_PASSWORD}".encode()).decode()}

# Check if the camera is online. If not, stop here
try:
    with urlopen(Request(CAMERA_URL, headers=auth_header)) as f:
        response = f.read().decode()
except HTTPError:
    raise
except URLError:
    sys.exit()

# Make a GET query to fetch the logs
log_url = f"{CAMERA_URL}/stslog_data.asp"
with urlopen(Request(log_url, headers=auth_header)) as f:
    response_log = f.read().decode()

# Use a regex to extract logs
log_entries = re.findall(r'logarr\[(\d+)\] = new logdata\("([^"]+)","([^"]+)"\);', response_log)

# Check if there is an error message
for index, hour, message in log_entries:
    if "-101" in message:
        print(f"Error message found: [{index}] {hour} {message}")
        print("We will restart the camera")
        break
else:
    print("No error found, exiting.")
    sys.exit()


def decode_base64(encoded_str):
    """Decode a base64 string."""
    return base64.b64decode(encoded_str).decode()


def jmd5(encode, key):
    """Calculate the token."""
    rk = ""
    for i in range(32):
        if (i % 4) == key:
            rk += encode[i]
    return rk


def cal_token(token1, token2, token3, token4):
    """Calculate the full token."""
    realtoken = []
    ret = ""

    realtoken.append(jmd5(token1, 0))
    realtoken.append(jmd5(token2, 1))
    realtoken.append(jmd5(token3, 2))
    realtoken.append(jmd5(token4, 3))

    for i in range(32):
        ret += realtoken[i % 4][i // 4]

    return ret


# Generate a random number between 1 and 200
TOKEN = random.randint(1, 200)

# Make the GET request to get the encoded string
get_url = f"{CAMERA_URL}/file_data.asp?{TOKEN}"
with urlopen(Request(get_url, headers=auth_header)) as f:
    response_get = f.read().decode()

# Extract the tokens with a regex
tokens = re.findall(r'var Token(\d+)=decodeBase64\("([^"]+)"\);', response_get)

# Decode each token
decoded_tokens = {int(token[0]): decode_base64(token[1]) for token in tokens}

# Check that we have at lease 4 tokens
if len(decoded_tokens) < 4:
    raise ValueError("Not enough decoded tokens.")

Token5, Token6, Token7, Token8 = decoded_tokens[5], decoded_tokens[6], decoded_tokens[7], decoded_tokens[8]

# Calculate the token header
token_header = cal_token(Token5, Token6, Token7, Token8)

# Make the POST request
post_url = f"{CAMERA_URL}/cgi/admin/wrestart.cgi"
post_headers = {
    "TOKEN": str(TOKEN) + "@" + token_header,
}

with urlopen(Request(post_url, headers={**post_headers, **auth_header}, method="POST")) as f:
    response_post = f.read().decode()

print("Camera restarted")
