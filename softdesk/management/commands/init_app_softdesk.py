from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from colorama import Fore, Style
import subprocess
import os
import re

from softdesk.models import Projects, Contributors, Issues, Comments


SUPERUSER_NAME = "admin"
SUPERUSER_PASSWORD = "applepie94"
SUPERUSER_EMAIL = "admin@bluelake.fr"
PROJECT_DIR = "."
DATABASE_NAME = "db.sqlite3"
DATABASE_PATH = f"{PROJECT_DIR}/{DATABASE_NAME}"
APPS = ['authentication', 'softdesk']


class Command(BaseCommand):
    help = "Script dédié à initialiser une base de données en environnement de développement."

    def handle(self, *args, **kwargs):
        print(f"{Fore.YELLOW}[REMOVING DATABASE]{Style.RESET_ALL}")
        if os.path.isfile(f"{DATABASE_PATH}"):
            subprocess.run(["rm", DATABASE_PATH])
            print(f"{Fore.GREEN}[DATABASE REMOVED]{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[NO DATABASE FOUND]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[REMOVING MIGRATIONS]{Style.RESET_ALL}")
        pattern = re.compile(r'([0]{3}).*py$')
        subprocess.run(["rm", "-rf", f"{PROJECT_DIR}/oc_projet10_rest_framework/__pycache__"])
        for app in APPS:
            subprocess.run(["rm", "-rf", f"{PROJECT_DIR}/{app}/__pycache__"])
            subprocess.run(["rm", "-rf", f"{PROJECT_DIR}/{app}/migrations/__pycache__"])
            for file in os.listdir(f"{app}/migrations/"):
                if re.match(pattern, file):
                    os.remove(f"{PROJECT_DIR}/{app}/migrations/{file}")
        print(f"{Fore.GREEN}[MIGRATIONS REMOVED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[PERFORMING MIGRATIONS]{Style.RESET_ALL}")
        subprocess.run(["python", "manage.py", "makemigrations"])
        print(f"{Fore.GREEN}[MIGRATIONS PERFORMED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[APPLYING MIGRATIONS TO DATABASE FOR APP: authentication]{Style.RESET_ALL}")
        subprocess.run(["python", "manage.py", "migrate", "authentication"])
        print(f"{Fore.GREEN}[MIGRATIONS APPLIED TO DATABASE]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[APPLYING MIGRATIONS TO DATABASE FOR APP: softdesk]{Style.RESET_ALL}")
        subprocess.run(["python", "manage.py", "migrate", "softdesk"])
        print(f"{Fore.GREEN}[MIGRATIONS APPLIED TO DATABASE]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[APPLYING MIGRATIONS TO DATABASE FOR GENERAL PURPOSE]{Style.RESET_ALL}")
        subprocess.run(["python", "manage.py", "migrate"])
        print(f"{Fore.GREEN}[MIGRATIONS APPLIED TO DATABASE]{Style.RESET_ALL}")

        User = get_user_model()
        users_list = [
            {
                "username": "donald.duck",
                "first_name": "donald",
                "last_name": "duck",
                "email": "donald.duck@bluelake.fr"
            },
            {
                "username": "daisy.duck",
                "first_name": "daisy",
                "last_name": "duck",
                "email": "daisy.duck@bluelake.fr"
            },
            {
                "username": "loulou.duck",
                "first_name": "loulou",
                "last_name": "duck",
                "email": "loulou.duck@bluelake.fr"
            },
        ]
        print(f"{Fore.YELLOW}[DUMMY SUPERUSER CREATION]{Style.RESET_ALL}")
        User.objects.create_superuser(SUPERUSER_NAME, SUPERUSER_EMAIL, SUPERUSER_PASSWORD)
        print(f"{Fore.GREEN}[DUMMY SUPERUSER CREATED]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[DUMMY USERS CREATION]{Style.RESET_ALL}")
        for user in users_list:
            User.objects.create_user(
                username=user["username"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                email=user["email"],
                password="applepie94"
            )
        print(f"{Fore.GREEN}[DUMMY USERS CREATED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[DUMMY PROJECTS CREATION]{Style.RESET_ALL}")
        # keep in mind that user 1 is the default admin
        projects_list = [
            {
                "title": f"Un 1er projet test de {User.objects.get(id=2).first_name}",
                "description": "bla bla bla",
                "type": "front-end IOS",
                "author_user_id": 2
            },
            {
                "title": f"Un 2eme projet test de {User.objects.get(id=2).first_name}",
                "description": "bla bla bla",
                "type": "back-end IOS",
                "author_user_id": 2
            },
            {
                "title": f"Un 1er projet test de {User.objects.get(id=3).first_name}",
                "description": "bla bla bla",
                "type": "front-end Android",
                "author_user_id": 3
            },
            {
                "title": f"Un 3eme projet test de {User.objects.get(id=2).first_name}",
                "description": "bla bla bla",
                "type": "front-end Android",
                "author_user_id": 2
            },
        ]
        for project in projects_list:
            preproject = Projects.objects.create(
                title=project["title"],
                description=project["description"],
                type=project["type"]
            )
            preproject.save()
            preproject.project_users.set([project["author_user_id"]])
            preproject.save()
            user = User.objects.get(id=project["author_user_id"])
            (Contributors.objects
                .filter(project_id=preproject.id)
                .filter(user_id=user.id)
                .update(permission="AUTHOR"))
            (Contributors.objects
                .filter(project_id=preproject.id)
                .filter(user_id=user.id)
                .update(role="responsable projet"))

        print(f"{Fore.GREEN}[DUMMY PROJECTS CREATED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[ADDING DUMMY USERS TO DUMMY PROJECTS]{Style.RESET_ALL}")
        # keep in mind that user 1 is the default admin
        # first we add user with id=3 to the project1 created by user with id=2
        user = User.objects.get(id=3)
        project = Projects.objects.get(id=1)
        Contributors.objects.create(
            user_id=user,
            project_id=project,
            permission="CONTRIBUTOR",
            role="contributeur projet"
        )
        # then we add user with id=4 to the project3 created by user with id=3
        user = User.objects.get(id=4)
        project = Projects.objects.get(id=3)
        Contributors.objects.create(
            user_id=user,
            project_id=project,
            permission="CONTRIBUTOR",
            role="contributeur projet"
        )
        print(f"{Fore.GREEN}[DUMMY USERS ADDED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[ADDING DUMMY ISSUES TO DUMMY PROJECTS]{Style.RESET_ALL}")
        user_author = User.objects.get(id=2)
        user_assignee = User.objects.get(id=4)
        project = Projects.objects.get(id=1)
        Issues.objects.create(
            title="1er problème à propos de la fonction affichage facture",
            desc="Phasellus posuere ultricies urna nec molestie. Ut nec leo pretium purus a, bibendum nulla.",
            tag="bug",
            priority="élevée",
            project_id=project,
            status="à faire",
            author_user_id=user_author,
            assignee_user_id=user_assignee
        )
        user_author = User.objects.get(id=3)
        user_assignee = User.objects.get(id=4)
        project = Projects.objects.get(id=3)
        Issues.objects.create(
            title="1er problème à propos de la version Android du client",
            desc="Phasellus posuere ultricies urna nec molestie. Ut nec leo pretium, dapibus purus a, bibendum nulla.",
            tag="amélioration",
            priority="moyenne",
            project_id=project,
            status="en cours",
            author_user_id=user_author,
            assignee_user_id=user_assignee
        )
        print(f"{Fore.GREEN}[DUMMY ISSUES ADDED]{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}[ADDING DUMMY COMMENTS TO DUMMY ISSUE]{Style.RESET_ALL}")
        issue = Issues.objects.get(id=1)
        project = Projects.objects.get(id=1)
        user = User.objects.get(id=2)
        Comments.objects.create(
            title="Dur comme 1ère tâche, bon courage",
            description="Aliquam eleifend mi sit amet ante maximus interdum. Fusce in diam euismod, scelerisque sem.",
            author_user_id=user,
            issue_id=issue
        )
        issue = Issues.objects.get(id=2)
        project = Projects.objects.get(id=3)
        user = User.objects.get(id=3)
        Comments.objects.create(
            title="Parler de nouveau avec le client",
            description="Nulla facilisi. Duis sollicitudin nunc et tincidunt. Proin viverra ex ut est finibus ?",
            author_user_id=user,
            issue_id=issue
        )
        issue = Issues.objects.get(id=2)
        project = Projects.objects.get(id=3)
        user = User.objects.get(id=4)
        Comments.objects.create(
            title="Besoin d'aide",
            description="Donec scelerisque ut magna vel auctor. Ut eu augue sit amet sapien eleifend feugiat sodales",
            author_user_id=user,
            issue_id=issue
        )
        print(f"{Fore.GREEN}[DUMMY COMMENTS ADDED]{Style.RESET_ALL}")
