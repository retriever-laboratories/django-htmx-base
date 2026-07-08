SECRET_KEY = "test-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django_htmx_base",
    "tests",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
