from rest_framework.permissions import BasePermission
from django.db.models import Q
from django.conf import settings
from datetime import date

from authentication.models import User
from softdesk.models import Projects, Contributors, Comments


class AssigneeUserIsContributor(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si un utilisateur est connu en tant que contributeur dans le projet.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        assignee_user_id = request.data['assignee_user_id']
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=assignee_user_id)
            .filter(role="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count > 0
        )


class UserCanViewProject(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie l'utilisateur peut consulter un projet.
        """
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
        """
        Description: on vérifie l'utilisateur peut consulter l'ensemble des projets.
        """
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class UserCanViewUser(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut consulter le profile des autres utilisateurs.
        """
        request_user_id = request.user.id
        user_to_view_id = request.resolver_match.kwargs['pk']
        try:
            user_to_view = User.objects.get(id=user_to_view_id)
        except Exception:
            # ce retour textuel n'est pas exploité. Un libellé était nécessaire pour permettre de jouer l'erreur 404.
            return "User not found"

        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id
            ) or (
                request.user and user_to_view.can_data_be_shared
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateUser(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut modifier le profile.
        """
        request_user_id = request.user.id
        user_to_view_id = request.resolver_match.kwargs['pk']
        try:
            user = User.objects.get(id=user_to_view_id)
        except Exception:
            return False

        user_has_majority = User.has_rgpd_min_age(user.birthdate)
        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id and user_has_majority
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )



class UserCanUpdateUserContactable(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut modifier son attribut 'can_be_contacted'.
        L'attribut donne ou non la possibilité d'être ajouté à un nouveau projet.
        """
        request_user_id = request.user.id
        user_to_view_id = request.resolver_match.kwargs['pk']
        try:
            user = User.objects.get(id=user_to_view_id)
        except Exception:
            return False

        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateUserDataSharing(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut modifier son attribut 'can_data_be_shared'.
        L'attribut donne ou non la possibilité d'avoir un profil utilisateur consultable.
        """
        request_user_id = request.user.id
        user_to_view_id = request.resolver_match.kwargs['pk']
        try:
            user = User.objects.get(id=user_to_view_id)
        except Exception:
            return False

        user_has_majority = User.has_rgpd_min_age(user.birthdate)
        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id and user_has_majority
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserNotAlreadyInProject(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur ajouté à un projet, n'y est pas déjà inscrit.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(role="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count == 0
        )


class UserCanDeleteProject(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie l'utilisateur a le droit de supprimer un projet spécifique.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(role="AUTHOR").count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanDeleteProjects(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie l'utilisateur a le droit de supprimer tous les projets.
        """
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )


class UserCanDeleteUserFromProject(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie l'utilisateur a le droit de retirer un contributeur du projet.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        user_to_remove = request.resolver_match.kwargs['user_id']
        project = Projects.objects.get(id=project_id)
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_to_remove)
            .filter(role="CONTRIBUTOR").count()
        )
        return bool(
            request.user and request.user.is_authenticated and contributor_count > 0
        )


class UserCanUpdateComment(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut modifier un commentaire.
        """
        user_id = request.user.id
        comment_id = request.resolver_match.kwargs['comment_id']
        comment = Comments.objects.get(id=comment_id)
        return bool(
            (
                request.user and request.user.is_authenticated and comment.author_user_id.id == user_id
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateIssue(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut mettre à jour un problème.
        """
        issue_id = request.resolver_match.kwargs['issue_id']
        user_id = request.user.id
        author_count = (
            Issues.objects
            .filter(id=issue_id)
            .filter(author_user_id=user_id)
            .filter(role="AUTHOR").count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateIssueStatus(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut mettre à jour le statut d'un problème.
        """
        issue_id = request.resolver_match.kwargs['issue_id']
        user_id = request.user.id
        issue_count = (
            Issues.objects
            .filter(id=issue_id)
            .filter(assignee_user_id=user_id).count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateProject(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut mettre à jour un projet.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(role="AUTHOR").count()
        )
        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateProjectUser(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut ajouter un utilisateur à un projet.
        """
        user_id = request.user.id
        user = User.objects.get(id=user_id)
        return bool(
            (
                request.user and request.user.is_authenticated and user.can_be_contacted
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )
