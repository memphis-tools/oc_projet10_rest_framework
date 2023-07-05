from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from werkzeug.security import generate_password_hash
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
import json
import uuid

from softdesk.permissions import UserCanUpdateProject, UserCanDeleteProject, UserCanDeleteProjects, \
    UserCanViewProject, UserCanUpdateProjectUser, UserCanDeleteUserFromProject, UserCanCreateIssue, \
    UserNotAlreadyInProject, AssigneeUserIsContributor, UserCanUpdateUser, UserCanViewUser, UserCanUpdateComment, \
    UserCanUpdateUserContactable, UserCanUpdateUserDataSharing, UserCanUpdateIssue, UserCanUpdateIssueStatus
from softdesk.serializers import RegisterUserSerializer, UserListSerializer, UserDetailSerializer, \
    UserUpdatePasswordSerializer, UserUpdateContactSerializer, UserUpdateDataSharingSerializer, \
    ProjectDetailSerializer, ProjectListSerializer, IssueSerializer, IssuesSerializer, \
    CommentListSerializer, CommentDetailSerializer, CommentUpdateSerializer, \
    ContributorUpdateSerializer, ContributorListSerializer
from softdesk.models import Projects, Issues, Comments, Contributors


class UserAPIView(APIView):
    """
    Description: dédiée à gérer la consultation ou la suppression d'un utilisateur.
    """
    permission_classes = [IsAuthenticated, UserCanUpdateUser | UserCanViewUser]
    serializer_class = UserListSerializer

    def get(self, request, pk, *args, **kwargs):
        try:
            queryset = get_user_model().objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewUser().has_permission(self.request, self, *args, **kwargs):
            serializer = UserDetailSerializer(queryset, many=False)
            return Response(serializer.data)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def delete(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateUser().has_permission(self.request, self, *args, **kwargs):
            user.delete()
            issues = Issues.objects.filter(assignee_user_id=pk)
            issues.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


class UserRegisterGenericsAPIView(generics.CreateAPIView):
    """
    Description: dédiée à gérer l'inscription d'utilisateur.
    """
    permission_classes = [AllowAny,]
    serializer_class = RegisterUserSerializer

    def get_queryset(self, *args, **kwargs):
        return get_user_model().objects.all()

    def get_serializer_class(self):
        return self.serializer_class


class UsersAPIView(APIView):
    """
    Description: dédiée à gérer la consultation ou la suppression des utilisateurs.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        paginator = LimitOffsetPagination()
        queryset = get_user_model().objects.all()
        if queryset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if self.request.user.is_superuser:
            result_page = paginator.paginate_queryset(queryset, request)
            serializer = UserListSerializer(result_page, many=True, context={'request': request})
        else:
            queryset = get_user_model().objects.filter(can_data_be_shared=True).exclude(id=1)
            result_page = paginator.paginate_queryset(queryset, request)
            serializer = UserListSerializer(result_page, many=True, context={'request': request})
        return Response(serializer.data)

    @transaction.atomic
    def delete(self, request, pk=None, *args, **kwargs):
        users = get_user_model().objects.filter(id__gte=2)
        if not users:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if self.request.user.is_superuser:
            users.delete()
            issues = Issues.objects.all()
            issues.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class UserUpdateContactGenericsAPIView(generics.UpdateAPIView):
    """
    Description: dédiée à permettre à un utilisateur de s'indiquer disponible à joindre un projet.
    """
    permission_classes = [IsAuthenticated, UserCanUpdateUserContactable]
    serializer_class = UserUpdateDataSharingSerializer

    def get_queryset(self, *args, **kwargs):
        return User.objects.all()

    def put(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdateContactSerializer(data=request.data, partial=True)
        if UserCanUpdateUserContactable().has_permission(self.request, self, *args, **kwargs):
            if serializer.is_valid():
                user.can_be_contacted = request.data['can_be_contacted']
                user.save()
                print(f"[DEBUG] user can_be_contacted is now eqquals to: {user.can_be_contacted}")
                return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
        message = {}
        print(f"[DEBUG] serializer=={serializer}")
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class UserUpdateDataSharingGenericsAPIView(generics.UpdateAPIView):
    """
    Description: dédiée à permettre à un utilisateur de partager ou non son profile aux autres utilisateurs connectés.
    """
    permission_classes = [IsAuthenticated, UserCanUpdateUserDataSharing]
    serializer_class = UserUpdateDataSharingSerializer

    def get_queryset(self, *args, **kwargs):
        return User.objects.all()

    def put(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdateDataSharingSerializer(user, data=request.data, partial=True)
        if UserCanUpdateUserDataSharing().has_permission(self.request, self, *args, **kwargs):
            if serializer.is_valid():
                user.can_data_be_shared = request.data['can_data_be_shared']
                user.save()
                return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
        message = {}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class UserUpdatePasswordGenericsAPIView(generics.UpdateAPIView):
    """
    Description: dédiée à permettre la mise à jour d'un mot de passe.
    """
    permission_classes = [IsAuthenticated,]
    serializer_class = UserUpdatePasswordSerializer

    def get_queryset(self, *args, **kwargs):
        return User.objects.all()

    def put(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = UserUpdatePasswordSerializer(user, data=request.data, context={'request': request})
        if serializer.is_valid():
            new_password = request.data['password']
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
            user.password = make_password(new_password)
            user.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)


class ProjectsUsersAPIView(APIView):
    """
    Description: dédiée à permettre l'ajout, la consultation, ou suppression d'un utilisateur à un projet.
    """
    permission_classes = [IsAuthenticated, UserCanUpdateProject | UserCanViewProject,]
    serializer_class = ContributorUpdateSerializer

    def get_queryset(self, *args, **kwargs):
        return Contributors.objects.all()

    def get(self, request, pk=None, user_id=None, *args, **kwargs):
        serializer = ProjectListSerializer()
        paginator = LimitOffsetPagination()
        if pk is None:
            if self.request.user.is_superuser:
                queryset = Contributors.objects.all()
                result_page = paginator.paginate_queryset(queryset, request)
                serializer = ContributorListSerializer(result_page, many=True, context={'request': request})
            else:
                queryset = Contributors.objects.all()
                if not queryset:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    result_page = paginator.paginate_queryset(queryset, request)
                    serializer = ContributorListSerializer(result_page, many=True, context={'request': request})
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        else:
            try:
                queryset = Contributors.objects.filter(project_id=pk)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = ContributorListSerializer(queryset, many=True)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = ContributorListSerializer(queryset, many=True)
                else:
                    message = []
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        try:
            Projects.objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserNotAlreadyInProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
                if UserCanUpdateProjectUser().has_permission(self.request, self, *args, **kwargs):
                    contributor_id = request.data['contributor_id']
                    try:
                        user = get_user_model().objects.get(id=contributor_id)
                    except Exception:
                        return Response(status=status.HTTP_404_NOT_FOUND)

                    if not user.can_be_contacted:
                        message = {"message": "utilisateur n'est plus disponible actuellement"}
                        return Response(message, status=status.HTTP_403_FORBIDDEN)
                    request.data["project_id"] = pk
                    request.data["user_id"] = user.id
                    request.data["role"] = "CONTRIBUTOR"
                    serializer = ContributorUpdateSerializer(data=request.data)
                    if serializer.is_valid():
                        serializer.save()
                        return Response(serializer.data)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def delete(self, request, pk=None, user_id=None, *args, **kwargs):
        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            contributors = (
                Contributors.objects
                .filter(project_id=pk)
                .filter(user_id=user_id)
                .filter(role="CONTRIBUTOR")
            )
            if not contributors:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if UserCanDeleteUserFromProject().has_permission(self.request, self, *args, **kwargs):
                contributors.delete()
                issues = Issues.objects.filter(assignee_user_id=user_id)
                issues.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                message = {}
                return Response(message, status=status.HTTP_403_FORBIDDEN)
        else:
            message = {}
            return Response(message, status=status.HTTP_403_FORBIDDEN)


class IssuesRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    """
    Description: dédiée à permettre la modification du statut d'un problème.
    """
    permission_classes = [IsAuthenticated, UserCanUpdateIssueStatus]
    serializer_class = IssueSerializer

    def get_queryset(self, *args, **kwargs):
        return Issues.objects.all()

    def put(self, request, pk, issue_id, *args, **kwargs):
        try:
            issue = Issues.objects.get(id=issue_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = IssueSerializer(issue, partial=True)
        if UserCanUpdateIssueStatus().has_permission(self.request, self, *args, **kwargs):
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_403_FORBIDDEN)
        message = {}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)


class IssuesAPIView(APIView):
    """
    Description: dédiée à permettre l'ajout, la consultation, modification ou suppression d'un problème.
    """
    permission_classes = [IsAuthenticated | UserCanCreateIssue | UserCanUpdateIssue]
    serializer_class = IssuesSerializer

    def get_queryset(self, *args, **kwargs):
        return Issues.objects.all()

    def get(self, request, pk, issue_id=None, *args, **kwargs):
        paginator = LimitOffsetPagination()
        if Issues.objects.filter(project_id=pk).count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if issue_id is None:
            try:
                queryset = Issues.objects.filter(project_id=pk)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                result_page = paginator.paginate_queryset(queryset, request)
                serializer = IssuesSerializer(result_page, many=True, context={'request': request})
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    result_page = paginator.paginate_queryset(queryset, request)
                    serializer = IssuesSerializer(result_page, many=True, context={'request': request})
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        else:
            try:
                queryset = Issues.objects.get(id=issue_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = IssuesSerializer(queryset, many=False)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = IssuesSerializer(queryset, many=True)
                else:
                    message = []
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        args_dict = json.loads(request.body)
        try:
            project = Projects.objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanCreateIssue().has_permission(self.request, self, *args, **kwargs):
            if AssigneeUserIsContributor().has_permission(self.request, self, *args, **kwargs):
                assignee_user_id = args_dict.pop("assignee_user_id")
                user = get_user_model().objects.get(id=assignee_user_id)
                author_user_id = request.user
                args_dict["project_id"] = project.id
                args_dict["assignee_user_id"] = user.id
                args_dict["author_user_id"] = author_user_id.id

                serializer = IssuesSerializer(data=args_dict, many=False)
                if serializer.is_valid():
                    serializer.save()
                else:
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                return Response(serializer.data)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk, issue_id, *args, **kwargs):
        args_dict = json.loads(request.body)
        try:
            Projects.objects.get(id=pk)
            issue = Issues.objects.get(id=issue_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateIssue().has_permission(self.request, self, *args, **kwargs):
            if AssigneeUserIsContributor().has_permission(self.request, self, *args, **kwargs):
                args_dict['project_id'] = pk
                serializer = IssuesSerializer(issue, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk, issue_id, *args, **kwargs):
        try:
            Projects.objects.get(id=pk)
            issue = Issues.objects.get(id=issue_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            issue.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            message = {}
            return Response(message, status=status.HTTP_403_FORBIDDEN)


class CommentsAPIView(APIView):
    """
    Description: dédiée à permettre l'ajout, la consultation, modification ou suppression d'un commentaire.
    """
    permission_classes = [IsAuthenticated,]

    def get_queryset(self, *args, **kwargs):
        return Comments.objects.all()

    def get(self, request, pk, issue_id, comment_id=None, *args, **kwargs):
        paginator = LimitOffsetPagination()
        if Issues.objects.filter(project_id=pk).count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if comment_id is None:
            try:
                Projects.objects.get(id=pk)
                Issues.objects.get(id=issue_id)
                queryset = Comments.objects.filter(issue_id=issue_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                result_page = paginator.paginate_queryset(queryset, request)
                serializer = CommentListSerializer(result_page, many=True, context={'request': request})
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    result_page = paginator.paginate_queryset(queryset, request)
                    serializer = CommentListSerializer(result_page, many=True, context={'request': request})
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            if not queryset:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            try:
                Projects.objects.get(id=pk)
                Issues.objects.get(id=issue_id)
                queryset = Comments.objects.filter(issue_id=issue_id).filter(id=comment_id)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if not queryset:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = CommentDetailSerializer(queryset, many=True)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = CommentDetailSerializer(queryset, many=True)
                else:
                    message = []
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, pk, issue_id, *args, **kwargs):
        args_dict = json.loads(request.body)
        comment_uuid = f"{uuid.uuid4()}"
        try:
            Projects.objects.get(id=pk)
            issue_id = Issues.objects.get(id=issue_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
            args_dict["uuid"] = comment_uuid
            args_dict["author_user_id"] = request.user.id
            args_dict["issue_id"] = issue_id.id
            serializer = CommentDetailSerializer(data=args_dict, many=False)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    def put(self, request, pk, issue_id, comment_id, *args, **kwargs):
        args_dict = json.loads(request.body)
        try:
            Projects.objects.get(id=pk)
            issue = Issues.objects.get(id=issue_id)
            comment = Comments.objects.get(id=comment_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateComment().has_permission(self.request, self, *args, **kwargs):
                args_dict['issue_id'] = issue_id
                serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk, issue_id, comment_id, *args, **kwargs):
        try:
            Projects.objects.get(id=pk)
            issue = Issues.objects.get(id=issue_id)
            comment = Comments.objects.get(id=comment_id)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateComment().has_permission(self.request, self, *args, **kwargs):
                comment.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


class ProjectsAPIView(APIView):
    """
    Description: dédiée à permettre l'ajout, la consultation, modification ou suppression d'un projet.
    """
    serializer_class = ProjectListSerializer
    detail_serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated | UserCanDeleteProject | UserCanDeleteProjects | UserCanUpdateProject, ]
    info = ""

    def get_queryset(self, *args, **kwargs):
        contributions_queryset = (
            Contributors.objects
            .filter(Q(user_id__in=[self.request.user.id]))
            .values_list('project_id')
        )
        projects_queryset = Projects.objects.filter(Q(id__in=contributions_queryset))
        return projects_queryset

    def get(self, request, pk=None, *args, **kwargs):
        paginator = LimitOffsetPagination()
        if Projects.objects.all().count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pk is None:
            if self.request.user.is_superuser:
                projects_queryset = Projects.objects.all()
                result_page = paginator.paginate_queryset(projects_queryset, request)
                serializer = ProjectListSerializer(result_page, many=True, context={'request': request})
            else:
                contributions_queryset = (
                    Contributors.objects
                    .filter(Q(user_id__in=[self.request.user.id]))
                    .values_list('project_id')
                )
                projects_queryset = Projects.objects.filter(Q(id__in=contributions_queryset))
                result_page = paginator.paginate_queryset(projects_queryset, request)
                serializer = ProjectListSerializer(result_page, many=True, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            try:
                project = Projects.objects.get(id=pk)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                queryset = Projects.objects.get(id=pk)
                serializer = ProjectDetailSerializer(queryset, many=False)
                return Response(serializer.data)
            else:
                user = self.request.user
                contributions_queryset = (
                    Contributors.objects
                    .filter(Q(user_id__in=[self.request.user.id]))
                    .values_list('project_id')
                )

                projects_queryset = Projects.objects.filter(Q(id__in=contributions_queryset))
                if project in projects_queryset:
                    queryset = Projects.objects.get(id=pk)
                    serializer = ProjectDetailSerializer(queryset, many=False)
                    return Response(serializer.data)
                message = {}
                return Response(message, status=status.HTTP_403_FORBIDDEN)

    def post(self, request, *args, **kwargs):
        user = get_user_model().objects.get(id=request.user.id)
        request.data["author_user_id"] = user.id
        serializer = ProjectDetailSerializer(data=request.data)

        if serializer.is_valid():
            project_id = serializer.save()
            Contributors.objects.create(
                user_id=user,
                project_id=project_id,
                role='AUTHOR',
            )
            Contributors.objects.create(
                user_id=user,
                project_id=project_id,
                role='CONTRIBUTOR',
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        try:
            project = Projects.objects.get(id=pk)
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = self.detail_serializer_class(project, data=request.data)
        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            message = {}
            return Response(message, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, pk=None, *args, **kwargs):
        if pk is None:
            total_projects = Projects.objects.all().count()
            if total_projects == 0:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if UserCanDeleteProjects().has_permission(self.request, self, *args, **kwargs):
                Projects.objects.all().delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                message = {}
                return Response(message, status=status.HTTP_403_FORBIDDEN)
        else:
            try:
                project = Projects.objects.get(id=pk)
            except Exception:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if UserCanDeleteProject().has_permission(self.request, self, *args, **kwargs):
                Projects.objects.get(id=pk).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                message = {}
                return Response(message, status=status.HTTP_403_FORBIDDEN)
