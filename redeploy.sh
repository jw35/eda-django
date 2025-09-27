#!/bin/bash -xe

. ~/.virtualenvs/eda-django/bin/activate

git pull

pip install -r requirements.txt

cd eda

export DJANGO_SETTINGS_MODULE=eda.production_settings

./manage.py collectstatic --no-input
./manage.py migrate

echo "Now reload from the web console"
echo ""
