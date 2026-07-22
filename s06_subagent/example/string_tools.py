import re


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug.

    - Converts text to lowercase
    - Replaces whitespace and hyphens with a single hyphen
    - Strips non-alphanumeric characters (except hyphens)
    - Strips leading/trailing hyphens
    """
    text = text.lower()
    text = re.sub(r'[\s-]+', '-', text)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text)
    text = text.strip('-')
    return text
