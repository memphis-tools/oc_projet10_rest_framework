from rest_framework.permissions import BasePermission
from django.db.models import Q

from authentication.models import User
from softdesk.models import Comments, Contributors, Projects, Issues


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
        try:
            project = Projects.objects.get(id=project_id)
        except Exception:
            return "Project not found"

        return bool(
            (
                request.user and request.user.is_authenticated and contributor_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
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
                request.user and user_to_view.can_profile_viewable
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

        return bool(
            (
                request.user and request.user.is_authenticated and request_user_id == user_to_view_id
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
        contributor_id = request.data["contributor_id"]
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=contributor_id)
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
        author_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(role="AUTHOR").count()
        )

        return bool(
            (
                request.user and request.user.is_authenticated and author_count > 0
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
            .filter(author_user_id=user_id).count()
        )

        return bool(
            (
                request.user and request.user.is_authenticated and author_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanUpdateIssueStatus(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut mettre à jour le statut d'un problème.
        """
        project_id = request.resolver_match.kwargs['pk']
        issue_id = request.resolver_match.kwargs['issue_id']
        user_id = request.user.id

        try:
            Projects.objects.get(id=project_id)
            Issues.objects.get(id=issue_id)
        except Exception:
            # ce retour textuel n'est pas exploité. Un libellé était nécessaire pour permettre de jouer l'erreur 404.
            return "Project or Issue not found"
        issue_assignee_user_count = (
            Issues.objects
            .filter(id=issue_id)
            .filter(assignee_user_id=user_id).count()
        )
        issue_author_user_count = (
            Issues.objects
            .filter(id=issue_id)
            .filter(author_user_id=user_id).count()
        )

        return bool(
            (
                request.user and request.user.is_authenticated and issue_assignee_user_count > 0
            ) or (
                request.user and request.user.is_authenticated and issue_author_user_count > 0
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class UserCanCreateIssue(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si l'utilisateur peut ajouter un problème à un projet.
        """
        project_id = request.resolver_match.kwargs['pk']
        user_id = request.user.id
        contributor_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
        ).count()

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
        author_count = (
            Contributors.objects
            .filter(project_id=project_id)
            .filter(user_id=user_id)
            .filter(role="AUTHOR").count()
        )

        return bool(
            (
                request.user and request.user.is_authenticated and author_count > 0
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
                request.user and request.user.is_authenticated and user.can_contribute_to_a_project
            ) or (
                request.user and request.user.is_authenticated and request.user.is_superuser
            )
        )


class ProjectCanBeUpdate(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si le projet est bien au statut Open.
        """
        project_id = request.resolver_match.kwargs['pk']
        project = Projects.objects.get(id=project_id)

        return bool(project.status == "Open")


class IssueCanBeUpdate(BasePermission):
    def has_permission(self, request, view):
        """
        Description: on vérifie si le problème n'est pas au statut "Finished"
        """
        issue_id = request.resolver_match.kwargs['issue_id']
        issue = Issues.objects.get(id=issue_id)

        return bool(issue.status != "Finished")
