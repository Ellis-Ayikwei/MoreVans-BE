from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response

class ApiConnectionStatusView(APIView):
    permission_classes = [AllowAny]
    def get(self, _):
        return Response({'status': 'Coonected to Morevans Api'})
