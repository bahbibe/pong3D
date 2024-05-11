from rest_framework.decorators import api_view
from .serializers import RegisterUserSerializer, UserSerializer, SetupProfileSerializer, LoginUserSerializer
from rest_framework.response import Response
from django.http import HttpResponse
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
import random
import string
import pyotp.totp
import qrcode

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
        if user is None or user.profile.auth_method == Profile.INTRA:
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
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user:
            return Response({"error": ["A user with this email already exists"]}, status=status.HTTP_400_BAD_REQUEST)
        
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
@is_authenticated
def logout_user(request):
    response = Response({"message": "User logged out"}, status=status.HTTP_200_OK)
    response.delete_cookie("access_token")
    return response


@api_view(["GET"])
@is_authenticated
def get_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
def login_intra(request):
    client_id = os.getenv("INTRA_CLIENT_ID")
    callback_uri = urllib.parse.quote(f"{os.getenv("API_URL")}/api/auth/intra/callback/", safe="")
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
    
    intra_response = requests.post("https://api.intra.42.fr/oauth/token", data={
        "grant_type": "authorization_code",
        "client_id": os.getenv("INTRA_CLIENT_ID"),
        "client_secret": os.getenv("INTRA_CLIENT_SECRET"),
        "code": code,
        "redirect_uri": f"{os.getenv('API_URL')}/api/auth/intra/callback/"
        })
    
    if intra_response.status_code != 200:
        return Response({"error": "Failed to get access token"}, status=status.HTTP_401_UNAUTHORIZED)
    
    json_response = intra_response.json()
    access_token = json_response["access_token"]
    if not access_token:
        return Response({"error": "No access token found"}, status=status.HTTP_401_UNAUTHORIZED)
    
    intra_response = requests.get("https://api.intra.42.fr/v2/me", headers={"Authorization": f"Bearer {access_token}"})
    if intra_response.status_code != 200:
        return Response({"error": "Failed to get user data"}, status=status.HTTP_401_UNAUTHORIZED)
    
    json_response = intra_response.json()
    user_data = {
        "username": json_response["login"],
        "email": json_response["email"],
        "first_name": json_response["first_name"],
        "last_name": json_response["last_name"],
        "avatar": json_response["image"]["link"]
    }
    
    user = User.objects.filter(username=user_data["username"]).first()
    if user.profile.auth_method != Profile.INTRA:
        user_data["username"] = f"{user_data['username']}_{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
        user = None
    
    if user is None:
        user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
            )
        Profile.objects.create(user=user, avatar=user_data["avatar"], auth_method=Profile.INTRA)
        user.set_unusable_password()
        user.save()
    
    access_token_liftime = datetime.now() + settings.ACCESS_TOKEN_LIFETIME
    access_token = generate_token({"id": user.id, "exp": access_token_liftime})
    response = redirect("http://localhost:3000/")
    response.set_cookie("access_token", access_token, httponly=True, expires=access_token_liftime)
    return response


@api_view(["GET"])
@is_authenticated
def enable_twofa(request):
    user = request.user
    if user.profile.is_tfa_enabled:
        return Response({"error": "2FA is already enabled"}, status=status.HTTP_400_BAD_REQUEST)
    
    secret = pyotp.random_base32()
    user.profile.is_tfa_enabled = True
    user.profile.tfa_secret = secret
    user.profile.save()
    tfa_code = pyotp.totp.TOTP(secret).provisioning_uri(user.username, issuer_name="ft_transcendence")
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
        )
    qr.add_data(tfa_code)
    qr.make(fit=True)
    tfa_image = qr.make_image(fill_color="black", back_color="white")
    # TODO: find a solution to show the user the qrcode one time only
    tfa_image.save(f"avatars/tfa/{user.username}.png")
    
    return Response({"message": "2FA enabled", "image": f"{os.getenv('API_URL')}/avatars/tfa/{user.username}.png"}, status=status.HTTP_200_OK)

@api_view(["POST"])
@is_authenticated
def verify_twofa(request):
    user = request.user
    if not user.profile.is_tfa_enabled:
        return Response({"error": "2FA is not enabled"}, status=status.HTTP_400_BAD_REQUEST)

    code = request.data.get("code")
    if not code:
        return Response({"error": "No code found"}, status=status.HTTP_400_BAD_REQUEST)
    
    is_code_valid = pyotp.TOTP(user.profile.tfa_secret).verify(code)
    if not is_code_valid:
        return Response({"error": "Invalid code"}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"message": "Code is valid"}, status=status.HTTP_200_OK)