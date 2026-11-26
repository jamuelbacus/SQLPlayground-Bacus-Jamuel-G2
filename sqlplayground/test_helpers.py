from html.parser import HTMLParser
from urllib.parse import urljoin


class _CsrfFormParser(HTMLParser):
    """Find the CSRF token in the form that posts to a given URL."""

    def __init__(self, current_url, target_url):
        super().__init__(convert_charrefs=True)
        self.current_url = current_url
        self.target_url = target_url
        self.token = None
        self._form_depth = 0
        self._token_depth = None

    def handle_starttag(self, tag, attrs):
        if tag == "form":
            self._form_depth += 1
            attributes = dict(attrs)
            method = (attributes.get("method") or "get").strip().lower()
            action = attributes.get("action")
            resolved_action = (
                urljoin(self.current_url, action) if action else self.current_url
            )
            if (
                self._token_depth is None
                and method == "post"
                and resolved_action == self.target_url
            ):
                self._token_depth = self._form_depth
            return

        if tag == "input" and self._form_depth == self._token_depth:
            attributes = dict(attrs)
            if (
                attributes.get("name") == "csrfmiddlewaretoken"
                and self.token is None
            ):
                self.token = attributes.get("value")

    def handle_endtag(self, tag):
        if tag == "form":
            if self._token_depth == self._form_depth:
                self._token_depth = None
            self._form_depth -= 1


def csrf_token_from_response(response, target_url):
    """Return the token rendered in the form that posts to target_url."""
    current_url = response.request["PATH_INFO"]
    parser = _CsrfFormParser(current_url, target_url)
    parser.feed(response.content.decode())
    if parser.token is None:
        raise AssertionError(f"CSRF token missing from POST form for {target_url}")
    return parser.token


def post_with_csrf_token(client, token_page_url, target_url, data):
    """GET a page with a token, then POST the data with that token."""
    page = client.get(token_page_url)
    assert page.status_code == 200, (
        f"Token page {token_page_url} returned status {page.status_code}"
    )
    token = csrf_token_from_response(page, target_url)
    return client.post(target_url, {**data, "csrfmiddlewaretoken": token})
