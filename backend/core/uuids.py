import uuid


def parse_uuid(value):
    """UUID from a URL part, or None when it is not a valid UUID."""
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None
