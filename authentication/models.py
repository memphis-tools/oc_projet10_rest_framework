from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from datetime import date


class User(AbstractUser):
    @staticmethod
    def has_rgpd_min_age(birthdate):
        today = date.today()
        y_bday, m_bday, d_bday = [int(item) for item in str(birthdate).split("-")]

        if today.year - y_bday < settings.RGPD_MIN_AGE:
            return False
        elif today.year - y_bday == settings.RGPD_MIN_AGE:
            if today.month > m_bday or (today.month == m_bday and today.day > d_bday):
                return False
        return True

    # We consider that an user which can be contacted, can be add to a project
    can_be_contacted = models.BooleanField(default=True)
    # We consider that an user whose datas can be shared, has a consultable profit ny any user connected.
    # Because of European RGPD any user younger than 16 can not be consultable by anybody but the admin.
    can_data_be_shared = models.BooleanField(default=True)
    birthdate = models.DateField(null=False)
    # When user subscribes he will have to fullfill his birthdate. We will then establish his /her age.
    # Because of European RGPD any user younger than 16 will need a parental approvement to participate.
    # In a development perspective we auto agree the parental approvement.
    # In a production perspective you must setup a parental approvement mecanism through the RegisterUserSerializer.
    has_parental_approvement = models.BooleanField(default=True)
    created_time = models.DateTimeField(default=now)
    projects_contributions_ids = models.ManyToManyField(
        'softdesk.Projects',
        through='softdesk.Contributors',
    )
