from django.urls import reverse
from django.test import Client
from django.conf import settings
from rest_framework import status
from time import sleep
import pytest

from authentication.models import User


@pytest.mark.django_db
class TestSignupAndLogin():
    user_data1 = {
        "username": "donald.duck",
        "first_name": "donald",
        "last_name": "duck",
        "birthdate": "2002-5-12",
        "email": "donald.duck@bluelake.fr",
        "password": "applepie94",
        "password2": "applepie94",
        "can_profile_viewable": True,
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
        "general_cnil_approvment": True
    }

    user_data4 = {
        "username": "louloute.duck",
        "first_name": "louloute",
        "last_name": "duck",
        "birthdate": "2015-5-12",
        "email": "louloute.duck@bluelake.fr",
        "password": "applepie94",
        "password2": "applepie94",
        "can_profile_viewable": True,
        "has_parental_approvement": False,
        "general_cnil_approvment": True
    }

    @pytest.mark.django_db
    def test_signup_user_older_rgpd_min_age(self):
        """
        Ensure we can create a new user.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, self.user_data1)
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.count() == 1
        assert User.objects.get().username == 'donald.duck'

    @pytest.mark.django_db
    def test_signup_user_younger_rgpd_min_age_without_parental_approvement_true(self):
        """
        Ensure a new user younger than RGPD min age can not signin without parental approvement.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, self.user_data4)
        assert response.status_code == 400

    @pytest.mark.django_db
    def test_password_hash_in_database(self):
        """
        Ensure that password is hashed in database.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, self.user_data1)

        password = "applepie94"
        db_user_password = User.objects.get(id=1).password
        assert db_user_password != password

    @pytest.mark.django_db
    def test_login(self):
        """
        Ensure we can login as a new user and that we obtain access with refresh tokens.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

        data = {"username": "louloute.duck", "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_refresh_token(self):
        """
        Ensure we can refresh the access token.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        refresh_token = response.data["refresh"]
        url = reverse('token_refresh')
        data = {"refresh": refresh_token}
        response = client.post(url, data=data)
        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" not in response.data

        data = {"refresh": "BeBopALula"}
        response = client.post(url, data=data)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_access_token_revocation_time(self):
        """
        Ensure the access token only valid within the ACCESS_TOKEN_LIFETIME time.
        Check your own settings, we set a default 5seconds lifetime
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        url = reverse('projects')
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get(url, headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_access_token_revocation_after_refresh(self):
        """
        Ensure an access token is no more valid after refresh.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        initial_access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        headers = {"Authorization": f"Bearer {initial_access_token}"}

        url = reverse('projects')
        response = client.get(url, headers=headers)
        assert response.status_code == 404

        url = reverse('token_refresh')
        data = {"refresh": refresh_token}
        response = client.post(url, data=data)
        new_access_token = response.data["access"]

        sleep(3)
        url = reverse('projects')
        response = client.get(url, headers=headers)
        assert response.status_code == 404

        sleep(3)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

        url = reverse('token_refresh')
        data = {"refresh": refresh_token}
        response = client.post(url, data=data)
        new_access_token = response.data["access"]

        url = reverse('projects')
        headers = {"Authorization": f"Bearer {new_access_token}"}
        response = client.get(url, headers=headers)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_get_users_list_without_authentication(self):
        """
        Ensure we can not get the users list without being authenticated.
        """
        client = Client()

        headers = {"Authorization": "Bearer BeBopALula"}
        url = reverse('users')
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_users_list_without_limit(self):
        """
        Ensure we can get the users list even without any limit specification.
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
        url = reverse('users')
        response = client.get(url, headers=headers)
        assert response.status_code == 200

        response = client.get('users/', headers=headers)
        assert response.status_code == 404

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        response = client.get(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_get_users_list_with_limit(self):
        """
        Ensure we can get the users list even with a limit specification.
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
        url = reverse('users')
        response = client.get(f"{url}?limit=2&offset=0", headers=headers)
        assert response.status_code == 200
        assert len(response.data) == 1

    @pytest.mark.django_db
    def test_authenticated_user_delete_his_account(self):
        """
        Ensure an authenticated user can delete his own account.
        Ensure that user does no more exist after deletion.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('users_detail', kwargs={"pk": 555})
        response = client.delete(url, headers=headers)
        assert response.status_code == 404

        url = reverse('users_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 204

        url = reverse('login')
        data = {"username": self.user_data2["username"], "password": self.user_data2["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('users_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 404

    @pytest.mark.django_db
    def test_authenticated_user_delete_an_other_account(self):
        """
        Ensure an authenticated user can not delete other users.
        Ensure that user does no more exist after deletion.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)

        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        headers = {"Authorization": f"Bearer {access_token}"}
        url = reverse('users_detail', kwargs={"pk": 2})
        response = client.delete(url, headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_delete_account(self):
        """
        Ensure an unauthenticated user can not delete an account.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)

        headers = {"Authorization": "Bearer BeBopALula"}
        url = reverse('users_detail', kwargs={"pk": 1})
        response = client.delete(url, headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_change_password_his_password(self):
        """
        Ensure an authenticated user can change his password. Ensure that the password still hashed
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)
        assert response.status_code == 201

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        headers = {"Authorization": f"Bearer {access_token}"}
        assert response.status_code == 200

        data = {"old_password": "applepie94", "password": "applepie94", "password2": "applepie94"}

        url = reverse('change_password', kwargs={"pk": 4})
        response = client.put(url, data=data, headers=headers, format='json')
        assert response.status_code == 404

        url = reverse('change_password', kwargs={"pk": 1})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 200

        password = "applepie94"
        db_user_password = User.objects.get(id=1).password
        assert db_user_password != password

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        url = reverse('change_password', kwargs={"pk": 1})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_change_password_other_user_password(self):
        """
        Ensure an authenticated user can not change an other user password.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)

        data = {"old_password": "applepie94", "password": "applepie94", "password2": "applepie94"}

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}

        url = reverse('change_password', kwargs={"pk": 2})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_change_password_his_password(self):
        """
        Ensure an unauthenticated user can not change an user password.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)

        data = {"can_profile_viewable": "False"}
        url = reverse('change_password', kwargs={"pk": 1})
        headers = {"Authorization": "Bearer BeBopALula"}
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_update_his_profile(self):
        """
        Ensure an authenticated user can change his profile.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)
        assert response.status_code == 201

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        access_token = response.data["access"]
        refresh_token = response.data["refresh"]
        headers = {"Authorization": f"Bearer {access_token}"}
        assert response.status_code == 200

        data = {"can_profile_viewable": "False"}

        url = reverse('users_detail', kwargs={"pk": 4})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 404

        url = reverse('users_detail', kwargs={"pk": 1})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 200
        assert response.data["can_profile_viewable"] is False

        sleep_time = settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]
        sleep(sleep_time.seconds)
        url = reverse('users_detail', kwargs={"pk": 1})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 401

    @pytest.mark.django_db
    def test_authenticated_user_update_other_user_profile(self):
        """
        Ensure an authenticated user can not update an other user profile.
        """
        client = Client()
        url = reverse('signup')
        response = client.post(url, data=self.user_data1)
        response = client.post(url, data=self.user_data2)
        assert response.status_code == 201

        url = reverse('login')
        data = {"username": self.user_data1["username"], "password": self.user_data1["password"]}
        response = client.post(url, data=data)
        access_token = response.data["access"]
        headers = {"Authorization": f"Bearer {access_token}"}
        assert response.status_code == 200

        data = {"can_profile_viewable": "False"}

        url = reverse('users_detail', kwargs={"pk": 2})
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_unauthenticated_user_update_other_user_profile(self):
        """
        Ensure an unauthenticated user can not update an user profile.
        """
        client = Client()
        url = reverse('signup')
        client.post(url, data=self.user_data1)

        data = {"can_profile_viewable": "False"}
        url = reverse('users_detail', kwargs={"pk": 1})
        headers = {"Authorization": "Bearer BeBopALula"}
        response = client.put(url, data=data, content_type="application/json", headers=headers)
        assert response.status_code == 401
