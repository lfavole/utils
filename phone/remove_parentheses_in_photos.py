"""
Rename pictures ending in (0), (1)... to remove the additional number
if the file doesn't exist.
"""
import glob
import os
import sys

if sys.platform == "linux" and os.path.exists("/data/data/com.termux"):
	files = glob.glob("/storage/emulated/0/DCIM/**/*(?).jpg") + glob.glob("/storage/*/DCIM/**/*(?).jpg")
else:
	files = glob.glob(os.path.expanduser("~").replace("\\", "/") + "/Pictures/**/*(?).jpg")

for file in files:
	real_file = file[:-7].strip() + ".jpg"
	if not os.path.exists(real_file):
		if sys.argv[1] == "ok":
			os.rename(file, real_file)
		else:
			print(file, "->", real_file)
			