from django.urls import resolve, reverse
from rest_framework import status
from rest_framework.test import APITestCase
from colorama import Fore, Style


def test_signup():
    """
    Ensure the signup view is UserRegisterGenericsAPIView.
    """
    path = reverse('signup')
    assert path == "signup/"
    assert resolve(path).view_name == "UserRegisterGenericsAPIView"

def test_login():
    """
    Ensure the login view is TokenObtainPairView.
    """
    path = reverse('login')
    assert path == "login/"
    assert resolve(path).view_name == "TokenObtainPairView"

def test_users_list():
    """
    Ensure the users list view is UsersAPIView.
    """
    path = reverse("users")
    assert path == "users/"
    assert resolve(path).view_name == "UsersAPIView"

def test_user_details():
    """
    Ensure the user details view is UserAPIView.
    """
    path = reverse("users_detail")
    assert path == "users/1"
    assert resolve(path).view_name == "UserAPIView"

def test_user_change_password():
    """
    Ensure the user details view is UserUpdatePasswordGenericsAPIView.
    """
    path = reverse("change_password")
    assert path == "users/1/change_password"
    assert resolve(path).view_name == "UserUpdatePasswordGenericsAPIView"

def test_projects_list():
    """
    Ensure the project list view is ProjectsAPIView.
    """
    path = reverse("projects")
    assert path == "projects/"
    assert resolve(path).view_name == "ProjectsAPIView"

def test_project_details():
    """
    Ensure the project details view is ProjectsAPIView.
    """
    path = reverse("projects_details")
    assert path == "projects/1/"
    assert resolve(path).view_name == "ProjectsAPIView"

def test_project_issues_list():
    """
    Ensure the project issues list view is IssuesAPIView.
    """
    path = reverse("issues")
    assert path == "projects/1/issues/"
    assert resolve(path).view_name == "IssuesAPIView"

def test_project_issue_details():
    """
    Ensure the project issue details view is IssuesAPIView.
    """
    path = reverse("issues_detail")
    assert path == "projects/3/issues/9"
    assert resolve(path).view_name == "IssuesAPIView"

def test_project_change_issue_status():
    """
    Ensure the issue change status view is IssuesRetrieveUpdateAPIView.
    """
    path = reverse("issues_status")
    assert path == "projects/3/issues/9/change_status/"
    assert resolve(path).view_name == "IssuesRetrieveUpdateAPIView"

def test_issue_comments_list():
    """
    Ensure the issue comments list view is CommentsAPIView.
    """
    path = reverse("issues")
    assert path == "projects/1/issues/3/comments/"
    assert resolve(path).view_name == "CommentsAPIView"

def test_issue_comment_details():
    """
    Ensure the issue comment details view is CommentsAPIView.
    """
    path = reverse("issues_detail")
    assert path == "projects/3/issues/9/comments/2/"
    assert resolve(path).view_name == "CommentsAPIView"
