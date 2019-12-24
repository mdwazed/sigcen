#!/bin/bash

echo "starting djnago"
python manage.py migrate
echo "migration complete"
echo "yes" | python manage.py collectstatic
echo "collect static complete"
# python manage.py runserver 0.0.0.0:8000
uwsgi --http :8000 --module tsp.wsgi
