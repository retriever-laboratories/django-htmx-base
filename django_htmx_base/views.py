from django.views.decorators.http import require_POST
from django.shortcuts import render

@require_POST
def ping(request):
    return render(request, "partials/ping_result.html", {"ok": True})
