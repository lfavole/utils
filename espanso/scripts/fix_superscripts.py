from html import escape
import re
import sys

num = int(sys.argv[1])
el = sys.argv[2]
html = int(sys.argv[3])

if num == 1:
    el = re.sub(r"^.*i?(?:[èeé](re?s?))?$", r"\1", el) or "er"
elif num == 2:
    el = re.sub(r"^.*(?:o?n)?(de?s?)$", r"\1", el) or "de"

if num >= 2:
    el = re.sub(r"^.*(?:i?[èeé]?m)?(es?)$", r"\1", el) or "e"

if html:
    print(f"{num}<sup>{escape(el)}</sup>")
else:
    print(f"{num}{el}")
