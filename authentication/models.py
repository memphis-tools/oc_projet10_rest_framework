from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    projects_contributions_ids = models.ManyToManyField(
        'softdesk.Projects',
        through='softdesk.Contributors',
    )
