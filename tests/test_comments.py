from django.urls import resolve, reverse
from django.test import Client
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from time import sleep
import uuid
import pytest

from authentication.models import User
from softdesk.models import Projects


@pytest.mark.django_db
class TestIssuesCrudAndAuthorization():
    user_data1 = {
        "username": "donald.duck",
        "first_name": "donald",
        "last_name": "duck",
        "birthdate": "2002-5-12",
        "email": "donald.duck@bluelake.fr",
        "password": "applepie94",
        "password2": "applepie94",
        "can_profile_viewable": True,
        "can_contribute_to_a_project": True,
        "general_cnil_approvment": True
    }

    user_data2 = {
        "username": "daisy.duck",
        "first_name": "daisy",
        "last_name": "duck",
        "birthdate": "2002-08-24",
        "email": "daisy.duck@bluelake.fr",
        "password": "applepie94",
        "password2": "applepie94",
        "can_profile_viewable": True,
        "can_contribute_to_a_project": True,
        "general_cnil_approvment": True
    }

    user_data3 = {
        "username": "fifi.duck",
        "first_name": "fifi",
        "last_name": "duck",
        "birthdate": "2012-5-12",
        "email": "fifi.duck@bluelake.fr",
        "password": "applepie94",
        "password2": "applepie94",
        "can_profile_viewable": True,
        "can_contribute_to_a_project": True,
        "has_parental_approvement": True,
        "general_cnil_approvment": True
    }

    project_data1 = {
        "title": f"Un 1er projet test de donald.duck",
        "description": "bla bla bla",
        "type": "front-end"
    }

    contributor_project1a = {
        "project_id": 1,
        "user_id": 2,
        "contributor_id": 2,
    }

    project_data2 = {
        "title": f"Un 1er projet test de daisy.duck",
        "description": "bla bla bla",
        "type": "back-end"
    }

    issue_data1 = {
        "title": "1er problème à propos de la fonction affichage facture",
        "description": "Phasellus posuere ultricies urna nec molestie. Ut nec leo pretium purus a, bibendum nulla.",
        "balise": "BUG",
        "priority": "HIGH",
        "project_id": "1",
        "status": "To Do",
        "author_user_id": "1",
        "assignee_user_id": "2"
    }

    comment_data1 = {
        "uuid": uuid.uuid4(),
        "title": "Dur comme 1ère tâche, bon courage",
        "description": "Aliquam eleifend mi sit amet ante maximus interdum. Fusce in diam euismod, scelerisque sem.",
        "author_user_id": "1",
    }

    comment_data1_update = {
        "title": "Dur comme 1ère tâche, prévoir un soutient externe.",
    }

    @pytest.mark.django_db
    def test_authenticated_user_create_comment_for_an_issue_when_part_of_project(self):
        """
        Ensure an authenticated user can create a comment for an issue in a project which he is the author or contributor.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_create_comment_for_an_issue_without_being_part_of_project(self):
        """
        Ensure an authenticated user can not create a comment for an issue if he either the author or contributor of project.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)
        client.post(url, data=self.user_data3)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_create_comment_for_an_issue(self):
        """
        Ensure an unauthenticated user can create a comment for an issue in a project which he is not either the author or contributor.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_view_comment_for_an_issue_when_part_of_project(self):
        """
        Ensure an authenticated user can view a comment for an issue in a project which he is the author or contributor.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_view_comment_for_an_issue_when_not_part_of_project(self):
        """
        Ensure an authenticated user can view a comment for an issue in a project which he is the author or contributor.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)
        client.post(url, data=self.user_data3)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}

        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_view_comment_for_an_issue(self):
        """
        Ensure an unauthenticated user can not view a comment for an issue.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_update_comment_for_an_issue_when_author(self):
        """
        Ensure an authenticated user can update a comment for an issue when he is the comment author.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.put(url, data=self.comment_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_update_comment_for_an_issue_when_not_author(self):
        """
        Ensure an authenticated user can not update a comment for an issue when he is not the comment author.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.put(url, data=self.comment_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_update_comment_for_an_issue(self):
        """
        Ensure an unauthenticated user can not update a comment for an issue.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.put(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_delete_comment_for_an_issue_when_author(self):
        """
        Ensure an authenticated user can delete a comment for an issue when he is the comment author.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 204

    @pytest.mark.django_db
    def test_authenticated_user_delete_comment_for_an_issue_when_not_author(self):
        """
        Ensure an authenticated user can not delete a comment for an issue when he is not the comment author.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)
        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_delete_comment_for_an_issue_when_not_author(self):
        """
        Ensure an unauthenticated user can not delete a comment for an issue.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)
        client.post(url, data=self.user_data2)
        client.post(url, data=self.user_data3)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments', kwargs={"pk": 1, "issue_id": 1})
        response = client.post(url, data=self.comment_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('comments_detail', kwargs={"pk": 1, "issue_id": 1, "comment_id": 1})
        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 401
