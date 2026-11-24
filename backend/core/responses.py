from django.http import JsonResponse
from rest_framework import status


def ErrorResponse(
    message: str = "Something went wrong!, Please try again later.",
    status_code: int = status.HTTP_400_BAD_REQUEST,
    serializer_errors=None,
) -> JsonResponse:
    """
    Returns a JSON response with a message and a status code.

    Args:
    message (str): The message to be returned in the JSON response.
    serializer_errors (dict): The serializer errors to be returned in the JSON response.
    status_code (int): The status code to be returned in the JSON response.
    """
    if serializer_errors is not None:
        new_serializer_errors = {}
        for key, value in serializer_errors.items():
            new_serializer_errors[key] = value[0]
        return JsonResponse(
            {
                "success": False,
                "message": message,
                "errors": new_serializer_errors,
            },
            status=status_code,
        )
    return JsonResponse(
        {
            "success": False,
            "message": message,
        },
        status=status_code,
    )


def SuccessResponse(
    data=None, message: str = "Success", status_code=status.HTTP_200_OK
) -> JsonResponse:
    """
    Returns a JSON response with a data and a status code.

    Args:
    message (str): The message to be returned in the JSON response.
    data (dict): The data to be returned in the JSON response.
    status_code (int): The status code to be returned in the JSON response.
    """
    if data is None:
        data = {}
    return JsonResponse(
        {
            "success": True,
            "message": message,
            "data": data,
        },
        status=status_code,
    )
