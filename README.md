# Competitor Monitor — Django mini project

Simple Django app featuring user authentication (signup, login, logout) backed by PostgreSQL.

## Features

- Signup/Login/Logout with Django auth
- Protected home page
- PostgreSQL persistence


## Tech stack

- Python 3.12+ (works on 3.13)
- Django 5.2
- PostgreSQL 13+
- VS Code (recommended)

## Quick start (Windows, PowerShell)

```powershell
# 1) Clone
git clone https://github.com/wahib-git/django-mini-project-competitor-monitor.git competitor-monitor
cd competitor-monitor

# 2) Virtual environment
py -m venv my_env
my_env\Scripts\Activate

# 3) Install deps
pip install django psycopg2

# If you have requirements.txt:
# pip install -r requirements.txt

# 4) Configure database (PostgreSQL)
# Create a DB and user (example)
# psql commands (run in your psql shell):
#   CREATE DATABASE competitor_monitor_db;
#   CREATE USER competitor_user WITH PASSWORD 'yourpassword';
#   GRANT ALL PRIVILEGES ON DATABASE competitor_monitor_db TO competitor_user;

# 5) Update settings.py DATABASES (example)
# See snippet below.

# 6) Migrations
py manage.py migrate

# 7) Superuser
py manage.py createsuperuser

# 8) Run server
py manage.py runserver
```

### Example DATABASES (settings.py)

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "competitor_monitor_db",
        "USER": "competitor_user",
        "PASSWORD": "yourpassword",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

## App URLs

- `/` → inscription (signup)
- `/connexion` → login
- `/acceuil` → protected home
- `/deconnexion` → logout
- `/admin` → Django admin



## Project structure (excerpt)

```
mini-project/
├─ auth_app/
│  ├─ templates/ (base.html, inscription.html, connexion.html, acceuil.html)
│  ├─ forms.py
│  ├─ views.py
│  └─ urls.py (optional if using project urls directly)
├─ competitor_monitor/
│  ├─ settings.py
│  ├─ urls.py
│  └─ static/ (style.css, favicon.ico)
└─ manage.py
```

## Tests (optional)

```powershell
# Example placeholders if you add tests later
py -m pip install pytest pytest-django
pytest
```


## Security notes

- Do not commit real secrets. Use environment variables for `SECRET_KEY` and DB credentials.
- Set `DEBUG = False` in production and configure `ALLOWED_HOSTS`.

---

Made with Django.
