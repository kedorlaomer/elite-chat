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
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`

## Deployment

For production deployment, use Gunicorn and Nginx. Static files are collected in the `staticfiles/` directory.

## License

This project is licensed under the MIT License.