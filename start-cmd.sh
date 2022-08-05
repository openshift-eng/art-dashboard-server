#!/usr/bin/env bash

export RUN_ENV=development
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:8080 --noreload
