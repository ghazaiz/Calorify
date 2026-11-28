from flask import request


def wants_json():
    """True only when the client explicitly prefers JSON over HTML.

    Browsers send Accept headers like ``text/html,...,*/*;q=0.8`` and must
    always receive the HTML page. Only API clients that rank
    ``application/json`` above ``text/html`` (e.g. ``Accept:
    application/json``) get a JSON response.
    """
    accept = request.accept_mimetypes

    return accept["application/json"] > accept["text/html"]
