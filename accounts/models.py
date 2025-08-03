from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username=None, password=None, role="service_provider", **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", role)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, username, password, **extra_fields) # Ensure superusers is not a client or serviceprovider

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    class UserRole(models.TextChoices):
        CLIENT = "client", "Client"
        SERVICE_PROVIDER = "service_provider", "Service Provider"
        ADMIN = "admin", "Admin"
    
    role = models.CharField(max_length=20, choices=UserRole.choices)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]