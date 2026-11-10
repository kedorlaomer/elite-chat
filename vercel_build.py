"""
Vercel build step (runs after dependencies are installed, before collectstatic).

Migrations only run for production deployments, so preview builds never touch
the production schema. The post_migrate hook in chat/apps.py then creates the
superuser from the DJANGO_SUPERUSER_* variables if none exists yet.
"""
import os
import subprocess
import sys


def manage(*args):
    subprocess.run([sys.executable, 'manage.py', *args], check=True)


def main():
    if os.environ.get('VERCEL_ENV') == 'production':
        manage('migrate', '--noinput')
    else:
        print(f"Skipping migrations for VERCEL_ENV={os.environ.get('VERCEL_ENV')!r}")


if __name__ == '__main__':
    main()
