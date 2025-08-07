from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from utilities.base_model import BaseModel


class AutoUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra_fields)


class Account(AbstractBaseUser, BaseModel, PermissionsMixin):
    username = models.CharField(max_length=50, unique=True)
    is_staff = models.BooleanField(default=False)
    access_token = models.CharField(
        max_length=32, unique=True, null=True, help_text="Access token for the user"
    )
    session_time = models.DateTimeField(null=True)
    USERNAME_FIELD = "username"
    objects = AutoUserManager()

    class Meta:
        db_table = "account"

    def __str__(self):
        return self.username
