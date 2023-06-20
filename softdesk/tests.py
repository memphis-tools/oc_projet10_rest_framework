from rest_framework.test import APITestCase, APIRequestFactory
from django.urls import reverse_lazy
from django.contrib.auth.models import User
from softdesk.models import Projects


class SoftdeskAPITest(APITestCase):

    factory = APIRequestFactory()

    @classmethod
    def setUpTestData(cls):
        # setup 2 users
        data = {
            "username": "donald.duck",
            "first_name": "donald",
            "last_name": "duck",
            "email": "donaldduck@local.lab",
            "password": "applepie94"
        }
        user1 = User(**data)
        user1.save()
        data = {
            "username": "daisy.duck",
            "first_name": "daisy",
            "last_name": "duck",
            "email": "daisyduck@local.lab",
            "password": "applepie94"
        }
        user2 = User(**data)
        user2.save()

        # setup 1 project and attach the user 1 as author
        data = {"title": "Projet test 1", "description": """
        In aliquam non tortor et venenatis. Nam imperdiet ex ligula, a faucibus augue consequat eu.
        Donec sapien tortor, dapibus sit amet dui non, efficitur dignissim lorem.
        Nam mattis nulla sit amet egestas ornare.
        Sed nec dignissim nunc. Aliquam vitae pulvinar risus.
        Duis vel nisl sollicitudin, porttitor neque eu, vestibulum ipsum.
        """, "type": "front-end"}
        project = Projects(**data)
        project.save()
        project.user_auth_id = user1.id
        project.save()


class UserTest(SoftdeskAPITest):
    url = reverse_lazy('projects-users-view-list')

    def test_list_users_without_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_create(self):
        users_count = User.objects.count()
        self.assertEqual(2, users_count)

    def test_delete(self):
        User.objects.get(username="daisy.duck").delete()
        users_count = User.objects.count()
        self.assertEqual(1, users_count)


class ProjectsTest(SoftdeskAPITest):
    url = reverse_lazy('projects-list')

    def test_list_projects_without_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_create(self):
        projects_count = Projects.objects.count()
        self.assertEqual(1, projects_count)

    def test_delete(self):
        Projects.objects.get(title="Projet test 1").delete()
        projects_count = Projects.objects.count()
        self.assertEqual(0, projects_count)


class ContributorsTest(SoftdeskAPITest):
    url = reverse_lazy("projects-users-view-list")

    def test_assign_user_to_project(self):
        user = User.objects.get(username="donald.duck")
        project = Projects.objects.get(title="Projet test 1")
        if all([user is not None, project is not None]):
            response = self.client.post(
                self.url,
                {'user_id': user.id, 'project_id': project.id, "permission": "author", "role": "responsable projet"}
            )

            self.assertEqual(response.status_code, 200)
