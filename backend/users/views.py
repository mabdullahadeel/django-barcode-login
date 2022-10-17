import datetime
from django.http import HttpRequest
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from users.models import User
from rest_framework import status
from users.serializers import UserPublicSerializer, UserCreateSerializer
from . import utils

TEN_MINUTES_IN_SECONDS = 60 * 10

class UserMeView(APIView):
    def get(self, request: HttpRequest) -> Response:
        user = UserPublicSerializer(request.user).data
        data = {
            "user": user
        }
        return Response(data=data, status=200)

class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = (AllowAny,)
    
    def create(self, request: HttpRequest, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        user = User.objects.get(username=serializer.data['username'])
        token = Token.objects.create(user=user).key
        return Response({"token": token}, status=status.HTTP_201_CREATED, headers=headers)


class CodeAuthView(APIView):
    permission_classes = (AllowAny,)
    
    def get(self, request: HttpRequest) -> Response:
        ws_cookie = request.COOKIES.get('ws_token', None)
        if ws_cookie and cache.has_key(ws_cookie):
            return Response({"ws_token": ws_cookie}, status=status.HTTP_200_OK)
        
        ws_token = utils.generate_random_string(5)
        while (cache.has_key(ws_token)):
            ws_token = utils.generate_random_string(5)
        cache.set(ws_token, '', timeout=TEN_MINUTES_IN_SECONDS)
        response =  Response({"ws_token": ws_token}, status=status.HTTP_200_OK)
        expires_in = datetime.datetime.utcnow() + datetime.timedelta(seconds=TEN_MINUTES_IN_SECONDS)
        response.set_cookie("ws_token", ws_token, path=request.path, httponly=True, expires=expires_in)
        return response

class CodeAuthLoginView(APIView):
    def post(self, request: HttpRequest) -> Response:
        ws_token = request.data['token']
        token = cache.get(ws_token)
        if (token):
            cache.delete(ws_token)
            auth_token = Token.objects.get(user=request.user).key
            return Response({"auth_token": auth_token}, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
