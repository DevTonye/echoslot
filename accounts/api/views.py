from django.shortcuts import render
from rest_framework.permissions import AllowAny
from ..serializers import RegisterSerializer, LoginSerializer, PasswordResetRequestSerializer, SetNewPasswordSerializer
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework import status
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from ..views import send_password_reset_link, send_verification_email
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from ..models import CustomUser
from django.shortcuts import render, redirect
User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        user = User.objects.get(id=response.data['id'])

        send_verification_email(user, request)

        return Response(
            {"detail": "Registration successful. Please check your email to verify your account."},
            status=status.HTTP_201_CREATED
        )
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh":str(refresh),
                "access": str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
            send_verification_email(user, request)
            return Response({"Verification link sent."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
             return Response(
                {"detail": "If this email exists, a verification link has been sent."}, 
                status=status.HTTP_200_OK
            )
        
class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")

        try:
            uid_decoded = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"error": "Invalid verification link."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": "Invalid or expired token."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user.is_active:
            return Response(
                {"message": "Email already verified."}, 
                status=status.HTTP_200_OK
            )

        user.is_active = True
        user.save()

        return Response(
            {"message": "Email verified successfully!"}, 
            status=status.HTTP_200_OK
        )
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                send_password_reset_link(user, request)
            except User.DoesNotExist:
                pass
            return Response({"detail": "If this email exists, a password reset link has been sent."}, status=status.HTTP_200_OK)
        
class PasswordResetConfirmAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = serializer.validated_data.get("new_password1")

        try:
            uid_decoded  = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid_decoded)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
        
        # validate password strength
        try:
             validate_password(new_password, user)
        except ValidationError as e:
            return Response({"error": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

class SelectUserRoleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.role:
            return Response({
                "detail": f"You already selected your role as {user.role}."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role = request.data.get("role")

        if role not in [CustomUser.UserRole.CLIENT, CustomUser.UserRole.SERVICE_PROVIDER]:
            return Response(
                {"error": "Invalid role. Choose either 'client' or 'service_provider'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()

        return Response(
            {"message": f"Role set to {user.role}. Please complete your profile."},
            status=status.HTTP_200_OK
        )