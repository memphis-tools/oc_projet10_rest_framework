from django.urls import resolve, reverse
from django.test import Client
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from time import sleep
import pytest

from authentication.models import User
from softdesk.models import Projects, Contributors, Issues, Comments


@pytest.mark.django_db
class TestProjectsCrudAndAuthorization():
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

    project_data1_update = {
        "description": "bla bla bla bla bla bla bla bla",
        "type": "iOS"
    }

    contributor_project1a = {
        "project_id": 1,
        "user_id": 2,
        "contributor_id": 2,
    }

    contributor_project1b = {
        "project_id": 1,
        "user_id": 15,
        "contributor_id": 15,
    }

    contributor_project2 = {
        "project_id": 2,
        "user_id": 1,
        "contributor_id": 1,
    }

    project_data2 = {
        "title": f"Un 1er projet test de daisy.duck",
        "description": "bla bla bla",
        "type": "back-end"
    }

    project_data3 = {
        "title": f"Un 2ème projet test de donald.duck",
        "description": "bla bla bla",
        "type": "iOS"
    }

    @pytest.mark.django_db
    def test_create_project_after_authentication(self):
        """
        Ensure an user can create a project. He must be author and contributor.
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
        assert Projects.objects.count() == 1
        contributors = Contributors.objects.filter(user_id=1)
        assert contributors[0].role == "AUTHOR"
        assert contributors[1].role == "CONTRIBUTOR"

        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_create_project_without_authentication(self):
        """
        Ensure an unauthenticated user can not create a project.
        """
        client = Client()
        headers = {"Authorization": f"Bearer BeBopALula"}
        url = reverse('projects')
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    @pytest.mark.parametrize("type", [("Interface web"), ("Windows"), ("FrOnT-EnD")])
    def test_create_project_with_wrong_type(self, type):
        """
        Ensure an authenticated user can not create a project with wrong type.
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
        data = {
            "title": f"Un 1er projet test de donald.duck",
            "description": "bla bla bla",
            "type": type
        }
        response = client.post(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_user_add_contributor_to_project_he_has_created(self):
        """
        Ensure an user can add a contributor to project which he created.
        We also check that only an existing user can be added, as a contributor.
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

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1b, content_type="application/json", headers=headers)
        assert response.status_code == 404

        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_add_contributor_to_project_he_has_not_created(self):
        """
        Ensure an user can not add a contributor to project he has not created.
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
        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 403

        headers = {"Authorization": f"Bearer BeBopALula"}
        response = client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_update_project_he_created(self):
        """
        Ensure an user can edit a project when he is an author.
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

        url = reverse('projects_detail', kwargs={'pk': 1})
        response = client.put(url, data=self.project_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 200
        project = Projects.objects.get(id=1)
        assert project.type == "iOS"

    @pytest.mark.django_db
    def test_user_update_project_he_has_not_created(self):
        """
        Ensure an user can not edit a project when he is not the author.
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
        url = reverse('projects_detail', kwargs={'pk': 1})
        response = client.put(url, data=self.project_data1_update, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_get_projects_list_without_limit(self):
        """
        Ensure an user can get the projects list which he creates or contributes without any limit specification.
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
        response = client.get(url, headers=headers)
        assert response.status_code == 404

        client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        client.post(url, data=self.project_data2, content_type="application/json", headers=headers)
        client.post(url, data=self.project_data3, content_type="application/json", headers=headers)

        response = client.get(url, headers=headers)
        assert response.status_code == 200
        assert len(response.data) == 3

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_projects_list_with_limit(self):
        """
        Ensure an user can get the projects list which he creates or contributes with a limit specification.
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
        client.post(url, data=self.project_data1, content_type="application/json", headers=headers)
        client.post(url, data=self.project_data2, content_type="application/json", headers=headers)
        client.post(url, data=self.project_data3, content_type="application/json", headers=headers)

        response = client.get(f"{url}?limit=1&offset=0", headers=headers)
        assert response.status_code == 200
        assert len(response.data) == 1

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_get_project_users_list_if_he_is_part_of_it(self):
        """
        Ensure an user can get the project users list as soon as he is part of the project.
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
        client.post(url, data=self.project_data1, content_type="application/json", headers=headers)

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_users', kwargs={"pk": 99})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_get_project_users_list_if_he_is_not_part_of_it(self):
        """
        Ensure an user can not get the project users list when he is not part of the project.
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
        client.post(url, data=self.project_data1, content_type="application/json", headers=headers)

        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.post(url, data=self.contributor_project1a, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('login')
        data = {"username": self.user_data3["username"], "password": self.user_data3["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects_users', kwargs={"pk": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_user_get_project_details_if_he_is_part_of_it(self):
        """
        Ensure an user can view project details when he is an author or contributor.
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
        response = client.post(url, data=self.project_data3, content_type="application/json", headers=headers)
        assert response.status_code == 200
        assert Projects.objects.count() == 2

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 200

        url = reverse('projects_detail', kwargs={"pk": 555})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_get_project_details_if_he_is_not_part_of_it(self):
        """
        Ensure an user can not view project details when he is not an author or contributor.
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
        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.get(url, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_user_delete_project_he_has_created(self):
        """
        Ensure an user can delete a project which he creates.
        Ensure then that the project does no more exist.
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
        response = client.post(url, data=self.project_data3, content_type="application/json", headers=headers)
        assert response.status_code == 200
        assert Projects.objects.count() == 2

        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 204
        assert Projects.objects.count() == 1

        response = client.delete(url, headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.delete(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_delete_project_he_has_not_created_but_where_he_is_contributor(self):
        """
        Ensure an user can not delete a project he has not created even if he is contributor.
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

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 403

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.delete(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_user_delete_project_he_has_not_created_and_is_not_contributor(self):
        """
        Ensure an user can not delete a project if he is not at all part of it.
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
        url = reverse('projects_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 403

        url = reverse('projects_detail', kwargs={"pk": 99})
        response = client.delete(url, headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.delete(url, headers=headers)
        assert response.status_code == 401
