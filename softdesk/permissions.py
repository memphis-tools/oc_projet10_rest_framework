from rest_framework.permissions import BasePermission
from django.db.models import Q
from softdesk.models import Projects, Contributors, Comments


class UserCanViewUser(BasePermission):
    def has_permission(self, request, view, *args, **kwargs):
        request_user_id = request.user.id
        user_to_view_id = request.resolver_match.kwargs['pk']
        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanViewProject(BasePermission):
    def has_permission(self, request, view, *args, **kwargs):
        project_id = request.resolver_match.kwargs['pk']
        project_contributions_count = Contributors.objects.filter(Q(user_id__in=[request.user.id])).count()
        user_id = request.user.id
        contributor_count = Contributors.objects.filter(project_id=project_id).filter(user_id=user_id).count()
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanViewProjects(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class UserNotAlreadyInProject(BasePermission):
    def has_permission(self, request, view):
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(permission="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count == 0
        )


class UserCanUpdateProject(BasePermission):
    def has_permission(self, request, view):
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(permission="AUTHOR").count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanDeleteUserFromProject(BasePermission):
    def has_permission(self, request, view):
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        user_to_remove = request.resolver_match.kwargs['user_id']
        project = Projects.objects.get(id=project_id)
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_to_remove)
            .filter(permission="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count > 0
        )


class UserCanDeleteProjects(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class UserCanDeleteProject(BasePermission):
    def has_permission(self, request, view, *args, **kwargs):
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(permission="AUTHOR").count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class AssigneeUserIsContributor(BasePermission):
    def has_permission(self, request, view, *args, **kwargs):
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        assignee_user_id = request.data['assignee_user_id']
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=assignee_user_id)
            .filter(permission="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count > 0
        )


class UserCanUpdateComment(BasePermission):
    def has_permission(self, request, view):
        user_id = request.user.id
        project_id = request.resolver_match.kwargs['pk']
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(permission="AUTHOR").count()
        )
        comment_id = request.resolver_match.kwargs['comment_id']
        comment = Comments.objects.get(id=comment_id)
        return bool(
            (
                request.user and request.user.is_authenticated and comment.author_user_id.id == user_id
            ) or (
                contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )
