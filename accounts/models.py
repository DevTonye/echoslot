from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, role="service_provider", **extra_fields):
        """Creates and saves a user with the given email, username and password."""
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", role)
        user = self.model(email=email,username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, username, password, **extra_fields) # Ensure superuser is not a client or serviceprovider

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True) # users must have a unique username

    class UserRole(models.TextChoices):
        CLIENT = "client", "Client"
        SERVICE_PROVIDER = "service_provider", "Service Provider"
        ADMIN = "admin", "Admin"
    
    role = models.CharField(max_length=20, choices=UserRole.choices)

    objects = CustomUserManager()

    USERNAME_FIELD = "email" # Use email instead of username for authentication
    REQUIRED_FIELDS = ["username"]