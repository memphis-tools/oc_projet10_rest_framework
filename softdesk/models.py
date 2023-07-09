from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import now


class Projects(models.Model):
    title = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(max_length=1850, null=False, blank=False)
    # type possible: back-end, front-end, iOS ou Android
    type = models.CharField(max_length=35, default="projet", null=False, blank=False)
    project_users = models.ManyToManyField(
        get_user_model(),
        through='Contributors',
    )
    # status possibles: Open, Archived, Canceled
    status = models.CharField(max_length=30, default="Open", null=False, blank=False)
    created_time = models.DateTimeField(default=now)


class Issues(models.Model):
    title = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(max_length=1850, null=False, blank=False)
    # balise possibles: BUG, TASK, FEATURE
    balise = models.CharField(max_length=25, null=False, blank=False)
    # priorité possible: LOW, MEDIUM, HIGH
    priority = models.CharField(max_length=25, null=False, blank=False)
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE)
    # status possibles: To Do, In Progress, Finished
    status = models.CharField(max_length=30, default="To Do", null=False, blank=False)
    author_user_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True)
    assignee_user_id = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='attributaire',
        null=True
    )
    created_time = models.DateTimeField(default=now)


class Comments(models.Model):
    uuid = models.UUIDField(null=False)
    title = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(max_length=1850, null=False, blank=False)
    author_user_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    issue_id = models.ForeignKey(Issues, on_delete=models.CASCADE)
    created_time = models.DateTimeField(default=now)


class Contributors(models.Model):
    AUTHOR = 'AUTHOR'
    CONTRIBUTOR = 'CONTRIBUTOR'
    PERMISSION_CHOICES = [
        (AUTHOR, 'auteur'),
        (CONTRIBUTOR, 'contributeur')
    ]
    user_id = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    project_id = models.ForeignKey(Projects, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=PERMISSION_CHOICES, verbose_name='role')
    created_time = models.DateTimeField(default=now)

    class Meta:
        unique_together = ('user_id', 'project_id', 'role')
