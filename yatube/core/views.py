from http import HTTPStatus
from django.shortcuts import render


def page_not_found(request, exception):
    return render(
        request, "core/404.html", {"path": request.path}, status=HTTPStatus.NOT_FOUND
    )


def csrf_failure(request, reason=""):
    return render(request, "core/403csrf.html")


def permission_denied(request, exception):
    """Настройка шаблона для страницы с ошибкой 403."""
    return render(request, "core/403.html", status=HTTPStatus.FORBIDDEN)
