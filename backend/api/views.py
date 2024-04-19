from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes, api_view
from .serializers import SetupProfileSerializer, UserSerializer
from rest_framework.response import Response
from rest_framework import status

@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def setup_profile(request):
    user = request.user
    serializer = SetupProfileSerializer(data=request.data)
    if serializer.is_valid():
        profile = user.profile
        profile.avatar = serializer.validated_data.get("avatar", profile.avatar)
        profile.is_setup = True
        profile.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)