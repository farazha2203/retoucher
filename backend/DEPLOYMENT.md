# Retoucher Backend Deployment Notes

## Environment variables

Copy `.env.example` to `.env` on the server and configure production values.

Required variables:

- `(^g-7t1!p$+kdv3wzz6c9c!_gisq*r785pi(wa!-!!&lf^b_!n`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

Recommended security variables:

- `DJANGO_SECURE_SSL_REDIRECT=True`
- `DJANGO_SESSION_COOKIE_SECURE=True`
- `DJANGO_CSRF_COOKIE_SECURE=True`
- `DJANGO_SECURE_HSTS_SECONDS=31536000`
- `DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True`
- `DJANGO_SECURE_HSTS_PRELOAD=True`

## Production checklist

```bash
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py create_demo_data --reset  # optional, demo/staging only