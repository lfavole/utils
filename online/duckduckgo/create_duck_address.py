# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests",
# ]
# ///
import re
from pathlib import Path

import requests

ua = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/113.0"}

token_file = Path(__file__).parent.resolve() / ".duckduckgo_token"

if token_file.exists():
    token = token_file.read_text("utf-8")
else:
    user = input("Username (without @duck.com): ").strip()
    resp = requests.get("https://quack.duckduckgo.com/api/auth/loginlink", {"user": user}, headers=ua)
    resp.raise_for_status()

    otp = re.sub(r"\s{2,}", " ", input("Please enter the OTP from the email: ").strip())
    resp = requests.get("https://quack.duckduckgo.com/api/auth/login", {"otp": otp, "user": user}, headers=ua)
    resp.raise_for_status()
    data = resp.json()
    token_req = data["token"]

    resp = requests.get("https://quack.duckduckgo.com/api/email/dashboard", headers={**ua, "Authorization": f"Bearer {token_req}"})
    resp.raise_for_status()
    data = resp.json()
    token = data["user"]["access_token"]
    token_file.write_text(token, "utf-8")

resp = requests.post("https://quack.duckduckgo.com/api/email/addresses", headers={**ua, "Authorization": f"Bearer {token}"})
resp.raise_for_status()
data = resp.json()
email = data["address"] + "@duck.com"
print(email)
