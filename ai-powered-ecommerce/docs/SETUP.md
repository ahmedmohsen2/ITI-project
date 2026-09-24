# Local setup

1. Install Python 3.11+ and PostgreSQL 14+.
2. Create a PostgreSQL database and user, then copy `.env.example` to `.env` and enter those connection values.
3. In the project directory, create/activate a virtual environment and run `pip install -r requirements.txt`.
4. Run `python manage.py migrate`, then optionally `python manage.py seed_demo`.
5. Create an administrator with `python manage.py createsuperuser`.
6. Start with `python manage.py runserver` and visit `http://127.0.0.1:8000/`.

For a disposable local demonstration without PostgreSQL, set `DB_ENGINE=sqlite` in `.env`. PostgreSQL remains the default and intended deployment database. Product images use external image URLs; uploaded media is not required by this implementation.
