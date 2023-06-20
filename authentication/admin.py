from django.contrib import admin
from django.contrib.auth.models import User


class UserAdminModel(admin.ModelAdmin):
    display = ["id", "username"]


admin.site.register(User, UserAdminModel)
