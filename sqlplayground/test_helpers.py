import re


def csrf_token_from_response(response):
    """Return the CSRF token rendered into a test response."""
    match = re.search(
        r'name="csrfmiddlewaretoken" value="([^"]+)"',
        response.content.decode(),
    )
    if match is None:
        raise AssertionError("CSRF token missing from response")
    return match.group(1)


def post_with_csrf_token(client, token_page_url, target_url, data):
    """GET a page with a token, then POST the data with that token."""
    page = client.get(token_page_url)
    return client.post(
        target_url,
        {**data, "csrfmiddlewaretoken": csrf_token_from_response(page)},
    )
