============
django-htmx-base
============

django-htmx-base is a Django app that includes a collection of classes and abstract models for django + htmx projects.

Detailed documentation is in the "docs" directory.

This README is currently focused on a local dist usage

Local Dist Quick start
-----------

1. Copy this package repository contents inside an existing django project
    ``cp -r django-htmx-base target-project/django-htmx-base`` 

2. Install the dist inside the target project
    with pip:
        ``python -m pip install --user django-htmx-base/dist/django_htmx_base.0.1.1.tar.gz``
    
    with uv
        ``uv add django-htmx-base/dist/django_htmx_base-0.1.1.tar.gz``

3. Add "django_htmx_base" to your INSTALLED_APPS setting like this:
    ```python
    INSTALLED_APPS = [
        ...,
	"django_htmx_base.apps.BaseConfig",
    ]
    ```

4. Import classes like "BaseModel" in your apps ´models.py´ file.
    ```python
    # Django
    from django.db import models
    
    # htmx base
    from django_htmx_base.models import BaseModel
    
    
    class MyModel(BaseModel):
        """
        Example Model Class
        """
    
        # fields
        name = models.CharField(
            max_length=256,
            unique=True,
        )
    ```

5. Run ``python manage.py makemigrations`` and ``python manage.py migrate`` to create the models.

