#!/bin/bash -xe

workon eda-django

git pull

pip install -r production-requirements.txt

cd eda

export DJANGO_SETTINGS_MODULE=eda.production_settings

./manage.py collectstatic --no-input
./manage.py migrate

echo "Now reload from the web console"
echo ""
