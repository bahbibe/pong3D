from rest_framework.decorators import api_view
from .serializers import RegisterUserSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Profile


class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = RegisterUserSerializer
    parser_classes = [MultiPartParser, FormParser]


@api_view(["POST"])
def register_user(request):
    serializer = RegisterUserSerializer(data=request.data)
    if serializer.is_valid():
        user = User.objects.create_user(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if "avatar" in serializer.validated_data:
            Profile.objects.create(
                user=user, avatar=serializer.validated_data["avatar"]
            )
        user.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_user(request):
    try:
        user = User.objects.get(id=4)
        return Response(UserSerializer(user).data)
        # return Response({"username": user.username, "email": user.email, "avatar": user.profile.avatar.url})
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
