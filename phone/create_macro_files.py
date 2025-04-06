"""
Split a MacroDroid backup file into many small macro and action block files.
"""
import json
from glob import glob

path = next(glob("/storage/emulated/0/AutoBackup/*.mdr"))
with open(path, "r") as f:
	data = json.loads(f.read())

for macro in data["macroList"]:
	with open("/storage/emulated/0/Macros/" + macro["m_name"].replace("*", "_").replace("/", "_") + (".ablock" if macro["isActionBlock"] else ".macro"), "w") as f:
		f.write(json.dumps(macro))
