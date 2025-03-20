# Symlink this directory to ~/.config/espanso
# Run this script to install the espanso configuration

espanso stop
mv ~/.config/espanso ~/.config/espanso.old
ln -s "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )" ~/.config/espanso
espanso start
