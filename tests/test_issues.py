from django.urls import reverse
from django.test import Client
import pytest

from softdesk.models import Projects, Issues


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
        "can_contribute_to_a_project": False,
        "has_parental_approvement": True,
        "general_cnil_approvment": True
    }

    project_data1 = {
        "title": "Un 1er projet test de donald.duck",
        "description": "bla bla bla",
        "type": "front-end"
    }

    contributor_project1a = {
        "project_id": 1,
        "user_id": 2,
        "contributor_id": 2,
    }

    project_data2 = {
        "title": "Un 1er projet test de daisy.duck",
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

    issue_data1_update = {
        "priority": "MEDIUM",
    }

    issue_data2 = {
        "title": "1er problème à propos de la fonction affichage facture",
        "description": "Phasellus posuere ultricies urna nec molestie. Ut nec leo pretium purus a, bibendum nulla.",
        "balise": "BUG",
        "priority": "HIGH",
        "project_id": "1",
        "status": "To Do",
        "author_user_id": "2",
        "assignee_user_id": "1"
    }

    @pytest.mark.django_db
    def test_authenticated_user_create_issue_when_author_or_contributor_of_project(self):
        """
        Ensure an authenticated user can create an issue in a project which he is the author or contributor.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data2, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "balise, priority, status", [
            ("BUGGY", "LOW", "To Do"),
            ("BUG", "NOT TOO HIGH", "To Do"),
            ("BUG", "LOW", "To Be Done ASAP"),
        ]
    )
    def test_authenticated_user_create_issue_but_with_wrong_data(self, balise, priority, status):
        """
        Ensure an authenticated user can not create an issue with wrong data.
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
        data = {
            "title": "1er problème à propos de la fonction affichage facture",
            "description": "Bla bla bla",
            "balise": balise,
            "priority": priority,
            "project_id": "1",
            "status": status,
            "author_user_id": "1",
            "assignee_user_id": "2"
        }
        response = client.post(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_authenticated_user_create_issue_when_not_author_or_contributor_of_project(self):
        """
        Ensure an authenticated user can not create an issue in a project if he is not author or contributor.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data2, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_create_issue(self):
        """
        Ensure an unauthenticated user can not create an issue in a project.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('issues', kwargs={"pk": 1})
        headers = {"Authorization": "Bearer BeBopALula"}
        response = client.post(url, data=self.issue_data2, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_he_created(self):
        """
        Ensure an authenticated user can update an issue he created.
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

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_he_has_not_created(self):
        """
        Ensure an authenticated user can update an issue he created.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_whereas_he_is_not_part_of_project(self):
        """
        Ensure an authenticated user which is not part of a project can not update an issue.
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

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_update_issue(self):
        """
        Ensure an unauthenticated user can not update an issue.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        headers = {"Authorization": "Bearer BeBopALula"}
        response = client.put(url, data=self.issue_data2, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_status_for_which_he_is_assigned(self):
        """
        Ensure an authenticated user can update an issue status when he is assigned to it.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues_status', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_status_for_which_he_is_not_assigned_but_is_the_author(self):
        """
        Ensure an authenticated user can update an issue status when he is not assigned but is the author.
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

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues_status', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_authenticated_user_update_issue_status_for_which_he_is_not_assigned_is_not_author(self):
        """
        Ensure an authenticated user can not update an issue status when he is not assigned to it and is not author.
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

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues_status', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_authenticated_user_delete_issue_he_created(self):
        """
        Ensure an authenticated user can delete an issue he created.
        Ensure the issue no more exist after deletion.
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

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 204

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_authenticated_user_delete_issue_he_has_not_created(self):
        """
        Ensure an authenticated user can not delete an issue he has not created.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_authenticated_user_delete_issue_whereas_he_is_not_part_of_project(self):
        """
        Ensure an authenticated user can not delete an issue he has not created.
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

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_delete_issue(self):
        """
        Ensure an authenticated user can not delete an issue he has not created.
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

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        headers = {"Authorization": "Bearer BeBopALula"}
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_add_issue_on_canceled_project(self):
        """
        Ensure user can add issue to an canceled project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Canceled"

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_add_issue_on_archived_project(self):
        """
        Ensure user can add issue to an archived project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Archived"

        url = reverse('issues', kwargs={"pk": 1})
        response = client.post(url, data=self.issue_data1, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_update_issue_on_canceled_project(self):
        """
        Ensure an authenticated user can not update an issue on a canceled project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Canceled"

        url = reverse('issues_status', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_update_issue_on_archived_project(self):
        """
        Ensure an authenticated user can not update an issue on an archived project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Archived"

        url = reverse('issues_status', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data=self.issue_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_delete_issue_on_canceled_project(self):
        """
        Ensure an authenticated user can not delete an issue on a canceled project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Canceled"

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_delete_issue_on_archived_project(self):
        """
        Ensure an authenticated user can not delete an issue on a archived project.
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

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        project = Projects.objects.get(id=1)
        assert response.status_code == 204
        assert project.status == "Archived"

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.delete(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    @pytest.mark.parametrize("status", [("To Do"), ("In Progress"), ("Finished")])
    def test_update_issue_status_with_expected_data(self, status):
        """
        Ensure a project status can be updated as 'To Do', 'In Progress', 'Finished'.
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

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data={"status": status}, content_type="application/json", headers=headers)
        issue = Issues.objects.get(id=1)
        assert response.status_code == 200
        assert issue.status == status

    @pytest.mark.django_db
    @pytest.mark.parametrize("status", [("progressing"), ("Open"), ("Unfinished"), ("Annulé")])
    def test_update_issue_status_with_unexpected_data(self, status):
        """
        Ensure a project status can only be updated as 'To Do', 'In Progress', 'Finished'.
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

        url = reverse('issues_detail', kwargs={"pk": 1, "issue_id": 1})
        response = client.put(url, data={"status": status}, content_type="application/json", headers=headers)
        issue = Issues.objects.get(id=1)
        assert response.status_code == 400
