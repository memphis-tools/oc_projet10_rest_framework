from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework import generics
from rest_framework import status
from rest_framework.response import Response
from werkzeug.security import generate_password_hash
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Q
import json

from softdesk.exceptions import ObjectDoesNotExistException
from softdesk.permissions import UserCanUpdateProject, UserCanDeleteProject, UserCanDeleteProjects, \
    UserCanViewProject, UserCanViewProjects, UserCanDeleteUserFromProject, UserCanViewUser, \
    UserNotAlreadyInProject, AssigneeUserIsContributor, UserCanUpdateComment
from softdesk.serializers import ProjectListSerializer, ProjectDetailSerializer, UserListSerializer, \
    UserUpdatePasswordSerializer, IssueSerializer, CommentListSerializer, CommentDetailSerializer, \
    RegisterUserSerializer, ContributorUpdateSerializer, ContributorListSerializer
from softdesk.models import Projects, Issues, Comments, Contributors


class RegisterUserGenericsAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny,]
    serializer_class = RegisterUserSerializer

    def get_queryset(self, *args, **kwargs):
        return get_user_model().objects.all()


class UserListAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser,]

    def get(self, request, *args, **kwargs):
        queryset = get_user_model().objects.all()
        if queryset is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = UserListSerializer(queryset, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def delete(self, request, pk=None, *args, **kwargs):
        users = get_user_model().objects.filter(id__gte=2)
        if not users:
            return Response(status=status.HTTP_404_NOT_FOUND)
        users.delete()
        issues = Issues.objects.all()
        issues.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserAPIView(APIView):
    permission_classes = [IsAuthenticated, UserCanViewUser,]
    serializer_class = UserListSerializer

    def get(self, request, pk, *args, **kwargs):
        try:
            queryset = get_user_model().objects.get(id=pk)
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if UserCanViewUser().has_permission(self.request, self, *args, **kwargs):
            serializer = UserListSerializer(queryset, many=False)
            return Response(serializer.data)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)

    @transaction.atomic
    def delete(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewUser().has_permission(self.request, self, *args, **kwargs):
            user.delete()
            issues = Issues.objects.filter(assignee_user_id=pk)
            issues.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


class UserUpdatePasswordGenericsAPIView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = UserUpdatePasswordSerializer

    def get_queryset(self, *args, **kwargs):
        return User.objects.all()

    def put(self, request, pk, *args, **kwargs):
        try:
            user = get_user_model().objects.get(id=pk)
        except ObjectDoesNotExistException:
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


class ProjectsUserAPIView(APIView):
    permission_classes = [IsAuthenticated | UserCanUpdateProject | UserCanViewProject | UserCanViewProjects,]
    serializer_class = ContributorUpdateSerializer

    def get_queryset(self, *args, **kwargs):
        return Contributors.objects.all()

    def get(self, request, pk=None, user_id=None, *args, **kwargs):
        serializer = ProjectListSerializer()
        if user_id is None:
            if self.request.user.is_superuser:
                queryset = Contributors.objects.filter(project_id=pk)
                serializer = ContributorListSerializer(queryset, many=True)
            else:
                queryset = Contributors.objects.filter(project_id=pk)
                if not queryset:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = ContributorListSerializer(queryset, many=True)
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        else:
            try:
                queryset = Contributors.objects.get(project_id=pk)
            except ObjectDoesNotExistException:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = ProjectDetailSerializer(queryset, many=True)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    queryset = Contributors.objects.filter(project_id=pk).filter(user_id=user_id)
                    serializer = ContributorListSerializer(queryset, many=True)
                else:
                    message = []
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        try:
            Projects.objects.get(id=pk)
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if UserNotAlreadyInProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
                contributor_id = request.data['contributor_id']
                user_role = request.data['role']

                try:
                    user = get_user_model().objects.get(id=contributor_id)
                except ObjectDoesNotExistException:
                    return Response(status=status.HTTP_404_NOT_FOUND)
                request.data["project_id"] = pk
                request.data["user_id"] = user.id
                request.data["role"] = user_role
                request.data["permission"] = "CONTRIBUTOR"
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
                .filter(permission="CONTRIBUTOR")
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


class ProjectsIssuesAPIView(APIView):
    permission_classes = [IsAuthenticated | UserCanUpdateProject]
    serializer_class = IssueSerializer

    def get_queryset(self, *args, **kwargs):
        return Issues.objects.all()

    def get(self, request, pk, issue_id=None, *args, **kwargs):
        if Issues.objects.filter(project_id=pk).count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if issue_id is None:
            try:
                queryset = Issues.objects.filter(project_id=pk)
            except ObjectDoesNotExistException:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = IssueSerializer(queryset, many=True)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = IssueSerializer(queryset, many=True)
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)
        else:
            try:
                queryset = Issues.objects.get(id=issue_id)
            except ObjectDoesNotExistException:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = IssueSerializer(queryset, many=False)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = IssueSerializer(queryset, many=True)
                else:
                    message = []
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            return Response(serializer.data)

    def post(self, request, pk, *args, **kwargs):
        args_dict = json.loads(request.body)
        try:
            project = Projects.objects.get(id=pk)
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            if AssigneeUserIsContributor().has_permission(self.request, self, *args, **kwargs):
                assignee_user_id = args_dict.pop("assignee_user_id")
                user = get_user_model().objects.get(id=assignee_user_id)
                author_user_id = request.user
                args_dict["project_id"] = project.id
                args_dict["assignee_user_id"] = user.id
                args_dict["author_user_id"] = author_user_id.id

                serializer = IssueSerializer(data=args_dict, many=False)
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
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            if AssigneeUserIsContributor().has_permission(self.request, self, *args, **kwargs):
                args_dict['project_id'] = pk
                serializer = IssueSerializer(issue, data=request.data, partial=True)
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
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            issue.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            message = {}
            return Response(message, status=status.HTTP_403_FORBIDDEN)


class ProjectsIssuesCommentAPIView(APIView):
    permission_classes = [IsAuthenticated,]

    def get_queryset(self, *args, **kwargs):
        return Comments.objects.all()

    def get(self, request, pk, issue_id, comment_id=None, *args, **kwargs):
        if Issues.objects.filter(project_id=pk).count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if comment_id is None:
            try:
                Projects.objects.get(id=pk)
                Issues.objects.get(id=issue_id)
                queryset = Comments.objects.filter(issue_id=issue_id)
            except ObjectDoesNotExistException:
                return Response(status=status.HTTP_404_NOT_FOUND)

            if self.request.user.is_superuser:
                serializer = CommentListSerializer(queryset, many=True)
            else:
                if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
                    serializer = CommentListSerializer(queryset, many=True)
                else:
                    message = {}
                    return Response(message, status=status.HTTP_403_FORBIDDEN)
            if not queryset:
                return Response(status=status.HTTP_404_NOT_FOUND)
            return Response(serializer.data)
        else:
            try:
                Projects.objects.get(id=pk)
                Issues.objects.get(id=issue_id)
                queryset = Comments.objects.filter(issue_id=issue_id).filter(id=comment_id)
            except ObjectDoesNotExistException:
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
        try:
            Projects.objects.get(id=pk)
            issue_id = Issues.objects.get(id=issue_id)
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
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
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanViewProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateComment().has_permission(self.request, self, *args, **kwargs):
                args_dict['issue_id'] = issue_id
                serializer = CommentDetailSerializer(comment, data=request.data, partial=True)
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
        except ObjectDoesNotExistException:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if UserCanUpdateProject().has_permission(self.request, self, *args, **kwargs):
            if UserCanUpdateComment().has_permission(self.request, self, *args, **kwargs):
                comment.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
        message = {}
        return Response(message, status=status.HTTP_403_FORBIDDEN)


class ProjectsAPIView(APIView):
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
        if Projects.objects.all().count() == 0:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pk is None:
            if self.request.user.is_superuser:
                queryset = Projects.objects.all()
                serializer = ProjectListSerializer(queryset, many=True)
            else:
                contributions_queryset = (
                    Contributors.objects
                    .filter(Q(user_id__in=[self.request.user.id]))
                    .values_list('project_id')
                )
                projects_queryset = Projects.objects.filter(Q(id__in=contributions_queryset))
                serializer = ProjectListSerializer(projects_queryset, many=True)
            return Response(serializer.data)

        else:
            try:
                project = Projects.objects.get(id=pk)
            except ObjectDoesNotExistException:
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
            contributors = Contributors.objects.create(
                user_id=user,
                project_id=project_id,
                permission='AUTHOR',
                role='Responsable projet'
            )
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, *args, **kwargs):
        try:
            project = Projects.objects.get(id=pk)
        except ObjectDoesNotExistException:
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
            except ObjectDoesNotExistException:
                return Response(status=status.HTTP_404_NOT_FOUND)
            if UserCanDeleteProject().has_permission(self.request, self, *args, **kwargs):
                Projects.objects.get(id=pk).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                message = {}
                return Response(message, status=status.HTTP_403_FORBIDDEN)
