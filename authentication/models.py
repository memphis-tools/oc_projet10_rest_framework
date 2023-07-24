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

    # Due to European RGPD and the use of this app we must obtain explicit consentment for
    # collecting data for a minor.
    general_cnil_approvement = models.BooleanField()

    # Due to European RGPD and the use of this app we must propose User if we want to be
    # contacted or not
    can_be_contacted = models.BooleanField(default=True)

    # Due to European RGPD and the use of this app we must propose User if we can share
    # his data
    can_data_be_shared = models.BooleanField(default=True)

    # When user subscribes he will have to fullfill his birthdate. We will then establish his /her age.
    # Because of European RGPD any user younger than 16 will need a parental approvement to participate.
    # In a development perspective we auto agree the parental approvement.
    # In a production perspective you must setup a parental approvement mecanism through the RegisterUserSerializer.
    birthdate = models.DateField(null=False)
    has_parental_approvement = models.BooleanField(default=True)
    # We consider that an user can decide to stay active but not add to any more project.
    can_contribute_to_a_project = models.BooleanField(default=True)
    # We consider that an user can decide that his profile details could not be seen by other users.
    can_profile_viewable = models.BooleanField(default=True)
    created_time = models.DateTimeField(default=now)
    projects_contributions_ids = models.ManyToManyField(
        'softdesk.Projects',
        through='softdesk.Contributors',
    )
