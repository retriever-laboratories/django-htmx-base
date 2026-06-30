from django.shortcuts import render
from django.views.decorators.http import require_POST


@require_POST
def ping(request):
    return render(request, "partials/ping_result.html", {"ok": True})
