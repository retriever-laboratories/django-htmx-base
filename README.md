# django-htmx-base

`django-htmx-base` is a lightweight Django library that provides viewsets, formsets, automated routers, and abstract models designed to eliminate CRUD boilerplate in Django + HTMX projects.


---

## Requirements

Before installing, ensure your environment meets the following requirements:
* **Python:** 3.12+
* **Django:** 6.0+
* **django-htmx:** 1.27+

---

## Installation & Quick Start

### 1. Installation

Install directly from GitHub via VCS (version 0.1.1):

**uv:**
```bash
uv add git+https://github.com
```

**pip:**
```bash
python -m pip install git+https://github.com
```

### 2. Configure Django Settings

Add the core application configuration and the required HTMX middleware to your project's `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    "django_htmx",
    "django_htmx_base",
]

MIDDLEWARE = [
    # ...
    "django_htmx.middleware.HtmxMiddleware",
]
```

---

## Usage Guide

### 1. Abstract Models

Inherit from `BaseModel` to quickly apply standard architecture baselines to your database layers:

```python
# my_app/models.py
from django.db import models
from django.urls import reverse
from django_htmx_base.models import BaseModel

class Product(BaseModel):
    name = models.CharField(max_length=256, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-id']
```

Execute your migrations normally inside your primary project environment:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Viewsets and Routing

Combine viewsets and routers to eliminate boilerplate URL configurations and automatically expose structural HTMX URLs to your templates.

```python
# my_app/views.py
from django_htmx_base.viewsets import GenericHtmxViewSet
from .models import Product

class ProductViewSet(GenericHtmxViewSet):
    """
    Handles standard CRUD actions and automatically provides 
    the `view.url_names` context object to your templates.
    """
    model = Product
```

#### Registering the Viewset

Use the `HTMXRouter` to map your viewset to standard URL endpoints seamlessly:

```python
# my_app/urls.py
from django.urls import path, include
from django_htmx_base.routers import HTMXRouter
from .views import ProductViewSet

router = HTMXRouter()
router.register(ProductViewSet)

app_name = "my_app"

urlpatterns = [
    path("products/", include(router.urls)),
]
```

### 3. Automated View Routing and Context

The viewset automatically discovers templates inside your application's `templates/[app_label]/` directory. Out of the box, it checks for a modern nested model directory first and falls back to a flat hyphenated filename. 

To enable generic, model-agnostic app fallbacks (e.g., sharing one `list.html` across multiple models), you must explicitly set `use_app_templates = True` on your viewset.

For a viewset handling a `Product` model inside a `products` app, the engine searches for templates in this order:

1. **Nested Model Folder (Default):** `templates/products/product/list.html`
2. **Flat Model Fallback (Default):** `templates/products/product-list.html`
3. **Generic App Fallback:** `templates/products/list.html` *(Requires `use_app_templates = True`)*

#### Example Viewset Configuration
```python
class ProductViewSet(GenericHtmxViewSet):
    model = Product
    
    # Optional: Enable the generic app-level fallback template
    use_app_templates = True 
```

Expose standard execution paths seamlessly to your user interface templates via integrated property-driven attributes:

```html
<!-- Generic Template Table Row Actions Component -->
{% for obj in object_list %}
<tr>
    <td>{{ obj.name }}</td>
    <td>
        <!-- Dynamically resolves view.basename + your htmx action settings safely -->
        <button hx-get="{% url view.url_names.edit pk=obj.pk %}" hx-target="#modal">Edit</button>
        <button hx-delete="{% url view.url_names.delete pk=obj.pk %}" hx-confirm="Are you sure?">Delete</button>
    </td>
</tr>
{% endfor %}
```

---

## Local Development & Contribution

If you want to modify this library, run its independent isolated test sandbox, or contribute fixes, set up your standalone repository workspace:

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com
cd django-htmx-base

# Create and activate a standard virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install the package in editable mode with test suites dependencies
pip install -e .[dev]
```

### 2. Running the Test Suite

Execute the local test suite runner directly via standard python commands:

```bash
python runtests.py
```

If you use the **uv** package manager, you can bypass explicit manual virtual environment setups entirely and execute everything inside an isolated wrapper on the fly:

```bash
uv run python runtests.py
```
