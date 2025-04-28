# Enable more debugging information
DEBUG = True
# Prevent logging to try to send emails to postgresql.org admins.
# Use the default Django logging settings instead.
LOGGING = None

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "archives",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "0.0.0.0",
    }
}

# Allow API access to all clients
PUBLIC_ARCHIVES = True
ALLOWED_HOSTS = ["*"]

PGWEB_ADDRESS = 'http://localhost:8001'
