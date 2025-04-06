import math
import subprocess as sp


def format_size(size: float):
    power = 1024
    n = 0
    labels = " KMGTPEZY"  # the " " is a placeholder
    while abs(size) > power:
        size /= power
        n += 1

    label = "" if n == 0 else labels[n]  # because of the placeholder
    digits = -int(math.log10(size / power)) if size else 0
    if n == 0:
        digits = 0  # no decimal part for bytes
    if digits == 0:
        size = int(size)  # remove the ".0"
    return f"{round(size, digits)} {label}B"


proc = sp.run(
    ["dpkg-query", "--show", "--showformat", r"${Installed-Size}\t${Package}\n"],
    check=True,
    stdout=sp.PIPE,
    text=True,
)
lines = [line.split("\t", 1) for line in proc.stdout.splitlines()]
lines = [(int(size) if size else 0, package) for size, package in lines]
lines = sorted(lines, key=lambda line: line[0])

for size, package in lines:
    # longest size = "123.4 kB" = 8 characters
    print(format_size(size * 1024).rjust(8) + "  " + package)
