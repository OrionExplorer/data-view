#!/bin/bash

# if [ "$DATABASE" = "postgres" ]
# then
#     echo "Waiting for PostgreSQL..."

#     while ! nc -z $SQL_HOST $SQL_PORT; do
#       sleep 0.1
#     done

#     echo "PostgreSQL started."
# fi

cd $HOME_DIR/data-view
# echo "Database flush..."
# python3 manage.py flush --no-input
# python3 manage.py migrate

echo "Collect static files..."
python3 manage.py collectstatic --noinput

echo "Apply database migrations..."
python3 manage.py migrate API

echo "Apply data-view application migrations..."
python3 manage.py makemigrations API
python3 manage.py migrate API

echo "Create default admin account..."
python3 manage.py initadmin

# echo "Run data-view services..."
# service cron start

# echo "Setting file permissions..."
# chmod +x permissions.sh
# ./permissions.sh
# ./run.sh

exec "$@"
