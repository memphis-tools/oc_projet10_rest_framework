from django.contrib import admin
from softdesk.models import Projects, Issues, Comments, Contributors


class ProjectsAdminModel(admin.ModelAdmin):
    display = ["id", "title"]


class IssuesAdminModel(admin.ModelAdmin):
    display = ["id", "title", "priority"]


class CommentsAdminModel(admin.ModelAdmin):
    display = ["id", "issue_id", "description"]


class ContributorsAdminModel(admin.ModelAdmin):
    display = ["id", "user_id", "project_id", "permission", "role"]


admin.site.register(Projects, ProjectsAdminModel)
admin.site.register(Issues, IssuesAdminModel)
admin.site.register(Comments, CommentsAdminModel)
admin.site.register(Contributors, ContributorsAdminModel)
