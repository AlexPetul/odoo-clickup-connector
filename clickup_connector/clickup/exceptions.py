from requests.exceptions import RequestException


class ClickupApiException(RequestException):
    pass
