"""OpenAPI helpers for the response envelope every view uses:
{"success": true, "message": "...", "data": ...} on success, and
{"success": false, "message": "...", "errors": {field: message}} on errors.
"""

from drf_spectacular.utils import inline_serializer
from rest_framework import serializers


class ErrorSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    errors = serializers.DictField(
        child=serializers.CharField(), required=False, help_text="One message per invalid field."
    )


def envelope(name, data=None, many=False):
    """A success response whose data is `data`: a serializer class or
    instance, a field, or None for a message only."""
    fields = {"success": serializers.BooleanField(), "message": serializers.CharField()}
    if isinstance(data, type) and issubclass(data, serializers.BaseSerializer):
        data = data(many=many)
    if data is not None:
        fields["data"] = data
    return inline_serializer(name=f"{name}Response", fields=fields)


def data_object(name, **fields):
    """An inline object for data, e.g. data_object("Game", game=GameSerializer())."""
    return inline_serializer(name=name, fields=fields)


def responses(name, data=None, many=False, errors=(400, 401)):
    """{200: envelope, <code>: ErrorSerializer ...} for extend_schema(responses=...)."""
    out = {200: envelope(name, data, many)}
    for code in errors:
        out[code] = ErrorSerializer
    return out
