# Generated by Django 4.2.2 on 2023-07-05 19:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Contributors',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('AUTHOR', 'auteur'), ('CONTRIBUTOR', 'contributeur')], max_length=20, verbose_name='role')),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='Projects',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(max_length=1850)),
                ('type', models.CharField(default='projet', max_length=35)),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('project_users', models.ManyToManyField(through='softdesk.Contributors', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Issues',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(max_length=1850)),
                ('balise', models.CharField(max_length=25)),
                ('priority', models.CharField(max_length=25)),
                ('status', models.CharField(default='To Do', max_length=30)),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('assignee_user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attributaire', to=settings.AUTH_USER_MODEL)),
                ('author_user_id', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('project_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='softdesk.projects')),
            ],
        ),
        migrations.AddField(
            model_name='contributors',
            name='project_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='softdesk.projects'),
        ),
        migrations.AddField(
            model_name='contributors',
            name='user_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Comments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField()),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(max_length=1850)),
                ('created_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('author_user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('issue_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='softdesk.issues')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='contributors',
            unique_together={('user_id', 'project_id', 'role')},
        ),
    ]
