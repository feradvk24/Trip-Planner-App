from urllib.parse import urlparse

def get_language_from_url(href):
    if not href:
        return "bg"
    parsed = urlparse(href)
    path_parts = parsed.path.strip("/").split("/")
    if path_parts and path_parts[0] in {"bg", "en"}:
        return path_parts[0]
    return "bg"