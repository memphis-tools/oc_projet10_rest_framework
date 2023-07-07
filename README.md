![Screenshot](python-django-rest-framework.svg)
# [OpenClassRoom](https://openclassrooms.com/) - Parcours développeur Python
![Screenshot](oc_parcours_dev_python.png)
## Projet 10 - Créer une API sécurisée RESTful en utilisant Django REST

### Project description
      Develop an opened access RESTful API which permits to supervise issues from 4 thematics: front-end, back-end, Android, or iOS.
      For each thematic you create a Project. For each ones, users can create issues and comments (as long as they are part of a project).
      So main features :
            - be able to create projetcs
            - add /remove user(s) from a specific project
            -,allow users to create issues and comments
            - endpoints which allows the dialog with the API

### Requirements
      Introduce all endpoints using Postman
      Quickly describe the code and how you manage to respect OWASP and RGPD guidelines.
      Introduce to your Postmand's API doc.
      Implement a dependency manager, example: pipenv or poetry.

### Competencies assessed
      - Create API RESTful with Django REST.
      - Securing an API with full respect of OWASP and RGPD guidelines.
      - Document an application through Postman.
      
---

## How use this project ?
1. Clone the repository

      `git clone https://github.com/memphis-tools/oc_projet10_rest_framework.git`

      `cd oc_projet10_rest_framework`

2. Setup a virtualenv : 2 possibilities offered here.

   2.1 Legacy (you create your venv, source it and then install project's dependencies)
   
      `python -m venv env`

      `source env/bin/activate`

      `pip install -U pip`

      `pip install -r requirements.txt`

   2.2 Poetry (you use poetry as a dependencie manager and as a venv builder)

      [https://python-poetry.org/docs/basic-usage/](https://python-poetry.org/docs/basic-usage/)
   
      This implies that you have already a Python interpreter and download the poetry package on your local machine: `pip install poetry`

      `poetry config cache-dir ./.cache/pypoetry --local`

      `poetry install`

      `poetry update`

      `source $(poetry env info --path)/bin/activate`
  
3. Start the application : 2 possibilities offered here.

   3.1 Start the application from scratch, run successively

      `python ./manage.py makemigrations`

      `python ./manage.py migrate`

      `python ./manage.py createsuperuser` (and follow instructions)

      `python ./manage.py runserver`

   3.2 Populate a development dummy database and then start the application

   Notice the 3 dummy users username: donald.duck, daisy.duck, loulou.duck. **Default password is:** applepie94 

      `python ./manage.py init_app_softdesk`

      `python ./manage.py runserver`

4. Read the postman [API documentation](https://documenter.getpostman.com/view/24090419/2s93sc4sWt)

      `Illustration`
![Screenshot](oc_projet10_postman_doc.png)

      `All run in a development environment`
![Screenshot](oc_projet10_postman_env_development.png)

5. Test the project

    `pytest tests -vs`

