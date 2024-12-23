#!/bin/bash
set -e

gitremote() {
    git -C "$FOLDER" remote "$@"
}

add_remote_to_repo() {
    FOLDER="$1"

    for remote in `gitremote`; do
        if [ "$remote" != "origin" ]; then
            echo "Removing $remote remote"
            gitremote remove "$remote"
        fi
    done

    R="$RANDOM"
    if [ ! "`gitremote`" ]; then
        echo "No remote, adding origin with URL $R"
        gitremote add origin "$R"
    else
        echo "Adding URL $R"
        gitremote set-url origin --add "$R"
        for url in `gitremote get-url origin --all`; do
            if [ "$url" != "$R" ]; then
                gitremote set-url origin --delete "$url"
            fi
        done
    fi

    for remote in "${REMOTES[@]}"; do
        if [ `basename "$FOLDER"` == "material-website" ]; then
            DOMAIN=`echo "$remote" | rev | cut -d. -f2- | rev`
            if [[ "$DOMAIN" =~ "codeberg" ]]; then
                DOMAIN+=".page"
            else
                DOMAIN+=".io"
            fi
            echo "Adding $remote URL (special: $USER.$DOMAIN)"
            gitremote set-url origin --add "git@$remote:$USER/$USER.$DOMAIN.git"
        else
            echo "Adding $remote URL"
            gitremote set-url origin --add "git@$remote:$USER/`basename $PWD`.git"
        fi
    done
    echo "Removing URL $R"
    gitremote set-url origin --delete "$R"
    echo "Pulling"
    git -C "$FOLDER" pull || echo "Failed to pull"
    echo "Setting upstream"
    git -C "$FOLDER" branch main --set-upstream-to origin/main || echo "Failed to set upstream"
}

TEMP=$(getopt -o 'r:' -l 'remote:' -n 'add-remotes.sh' -- "$@")
eval set -- "$TEMP"
unset TEMP

REMOTES=()

while true; do
	case "$1" in
		'-r'|'--remotes')
			echo "Remote: '$2'"
            REMOTES+=( "$2" )
			shift 2
			continue
		;;
		'--')
			shift
			break
		;;
		*)
			echo 'Internal error!' >&2
			exit 1
		;;
	esac
done

if [ -z "${REMOTES[@]}" ]; then
    echo "No remotes specified, using defaults"
    REMOTES=("github.com" "gitlab.com" "codeberg.org")
fi

for arg; do
    if [ ! -d "$arg" ]; then
        echo "'$arg' is a file, skipping";
        continue
    fi
	echo "Processing folder '$arg'"
    add_remote_to_repo "$arg"
    echo
done
