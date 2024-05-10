from rest_framework.decorators import api_view
from .serializers import RegisterUserSerializer, UserSerializer, SetupProfileSerializer, LoginUserSerializer
from rest_framework.response import Response
from django.http import JsonResponse
from rest_framework import status, viewsets
from django.contrib.auth.models import User
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Profile
from django.shortcuts import redirect
from django.contrib.auth.hashers import check_password
from .auth_utils import generate_token, is_authenticated
from django.conf import settings
from datetime import datetime
import urllib.parse
import requests
import os

class RegisterUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = SetupProfileSerializer
    parser_classes = [MultiPartParser, FormParser]


@api_view(["POST"])
def login_user(request):
    serailizer = LoginUserSerializer(data=request.data)
    
    if serailizer.is_valid():
        custom_validataion = serailizer.validated_data.get("email") is not None or serailizer.validated_data.get("username") is not None
        if not custom_validataion:
            return Response({"error": ["An email or username is required to log in."]}, status=status.HTTP_400_BAD_REQUEST)
        
        auth_field = "email" if serailizer.validated_data.get("email") is not None else "username"
        user = User.objects.filter(**{auth_field: serailizer.validated_data.get(auth_field)}).first()
        if user is None:
            return Response({"error": ["These credentials does not match any records"]}, status=status.HTTP_404_NOT_FOUND)
        
        is_password_valid = check_password(serailizer.validated_data.get("password"), user.password)
        if not is_password_valid:
            return Response({"error": ["These credentials does not match any records"]}, status=status.HTTP_404_NOT_FOUND)
        
        access_token_liftime = datetime.now() + settings.ACCESS_TOKEN_LIFETIME
        access_token = generate_token({"id": user.id, "exp": access_token_liftime})
        response = Response({"access_token": access_token}, status=status.HTTP_200_OK)
        response.set_cookie("access_token", access_token, httponly=True, expires=access_token_liftime)
        return response
    
    return Response(serailizer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def register_user(request):
    serializer = RegisterUserSerializer(data=request.data)
    
    if serializer.is_valid():
        user = User.objects.create_user(
            username=serializer.validated_data["username"],
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        Profile.objects.create(user=user)
        user.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def logout_user(request):
    pass


@api_view(["GET"])
@is_authenticated
def get_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def login_intra(request):
    client_id = os.getenv("INTRA_CLIENT_ID")
    callback_uri = urllib.parse.quote(f"{os.getenv("API_URL")}/auth/intra/callback/", safe="")
    auth_url = f"https://api.intra.42.fr/oauth/authorize?client_id={client_id}&redirect_uri={callback_uri}&response_type=code"
    return Response({"url": auth_url}, status=status.HTTP_200_OK)


@api_view(["GET"])
def login_intra_callback(request):
    code = request.GET.get("code")
    error = request.GET.get("error")
    if error:
        return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)
    if not code:
        return Response({"error": "No code found"}, status=status.HTTP_400_BAD_REQUEST)
    """
        TODO: Get the user data
        - post request to https://api.intra.42.fr/oauth/token with the following data:
            - grant_type : authorization_code
            - client_id : your client id
            - client_secret : your client secret
            - code : the code you got from the previous request
        - then get the access token and get the user information
    """
    intra_response = requests.post("https://api.intra.42.fr/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": os.getenv("INTRA_CLIENT_ID"),
        "client_secret": os.getenv("INTRA_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": f"{os.getenv('API_URL')}/auth/intra/callback/"
        })
    if intra_response.status_code != 200:
        return Response({"error": "Failed to get access token"}, status=status.HTTP_401_UNAUTHORIZED)
    json_response = intra_response.json()
    access_token = json_response["access_token"]
    if not access_token:
        return Response({"error": "No access token found"}, status=status.HTTP_401_UNAUTHORIZED)
    """
        get user data and create a user in the database if it doesn't exist
        then generate the tokens and return them
        TODO: check if user is already authenticated
    """
    intra_response = requests.get("https://api.intra.42.fr/v2/me", headers={"Authorization": f"Bearer {access_token}"})
    if intra_response.status_code != 200:
        return Response({"error": "Failed to get user data"}, status=status.HTTP_401_UNAUTHORIZED)
    json_response = intra_response.json()
    user_data = {
        "username": json_response["login"],
        "email": json_response["email"],
        "first_name": json_response["first_name"],
        "last_name": json_response["last_name"],
        "image": json_response["image"]["link"]
    }
    print("user data =====> ", user_data)
    return redirect("http://localhost:3000/login")
