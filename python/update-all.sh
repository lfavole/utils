pip freeze --user --disable-pip-version-check | sed 's/==.*//' | xargs pip install --user --upgrade
