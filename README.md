# Elite Chat

Elite Chat is a premium chat forum software built with Django. It allows users to create and join chat rooms, post messages, and engage in discussions. Features include user authentication, room management, message approval system, and internationalization support.

## Features

- User registration and authentication
- Chat rooms with membership management
- Message posting with approval workflow
- Admin interface for moderation
- Internationalization (i18n) support
- Responsive design

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run migrations: `DEBUG=true python manage.py migrate` (uses `db.sqlite3` unless `DATABASE_URL` is set)
4. Create superuser: set `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD`, then `python manage.py createsuperuser`
5. Run server: `DEBUG=true python manage.py runserver`

Tests: `DEBUG=true python manage.py test chat`

## Configuration

| Variable | Required | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | yes, unless `DEBUG=true` | Django secret key |
| `DATABASE_URL` | in production | Postgres URL; use a pooled endpoint on serverless hosts |
| `ALLOWED_HOSTS` | in production | Comma-separated host names; Vercel deployment URLs are added automatically |
| `DJANGO_SUPERUSER_USERNAME`, `_EMAIL`, `_PASSWORD` | first deploy | Superuser created after migrations if none exists |
| `CHAT_POLL_INTERVAL_MS` | no | Poll interval for a visible room tab (default 5000) |
| `CHAT_POLL_HIDDEN_INTERVAL_MS` | no | Poll interval for a hidden tab (default 30000) |
| `DEBUG` | no | `true` for local development only |

Rooms update by polling `room/<id>/messages/?since=<cursor>`, which returns new and changed messages and the ids of deleted ones. There is no WebSocket server.

## Deployment

The app deploys to Vercel as a single Python function (WSGI). Vercel detects Django from `manage.py`, runs `vercel_build.py` (migrations, production only) and `collectstatic`, and serves static files from its CDN.

Compiled translations (`locale/*/LC_MESSAGES/django.mo`) are committed because the build image has no GNU gettext; run `python manage.py compilemessages` after editing a `.po` file.

Uploaded images are stored in the database and limited to 4 MB (Vercel's request body limit is 4.5 MB).

`start.sh` still runs the app under Gunicorn on a regular server or container host.

## License

This project is licensed under the MIT License.