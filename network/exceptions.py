from rest_framework.exceptions import ValidationError
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Return every error as {"error": "..."} like the 404 response in the spec.
    Validation errors also keep the field wise errors under "details"."""
    response = exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = {"error": "Validation Error", "details": response.data}
    elif isinstance(response.data, dict) and "detail" in response.data:
        response.data = {"error": str(response.data["detail"])}

    return response
