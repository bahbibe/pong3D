from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(["GET"])
def get_data(request):
    message = {"message": "Hello, world!"}
    return Response(message)

@api_view(["POST"])
def post_data(request):
    message = request.data
    return Response(message)