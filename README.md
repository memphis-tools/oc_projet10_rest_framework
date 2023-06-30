# [OpenClassRoom](https://openclassrooms.com/) - Parcours développeur Python
![Screenshot](oc_parcours_dev_python.png)
## Projet 10 - Créer une API sécurisée RESTful en utilisant Django REST

### Description projet
      Développer une application de suivi des problèmes pour les trois plateformes (site web, applications Android et iOS).
      L'application permettra essentiellement aux utilisateurs :
            - de créer divers projets, 
            - d'ajouter des utilisateurs à des projets spécifiques, 
            - de créer des problèmes au sein des projets et d'attribuer des libellés à ces problèmes en fonction de leurs priorités, de balises, etc.
      Les trois applications exploiteront les points de terminaison d'API qui serviront les données.
      Principales fonctionnalités de l'application :
      
| id | Fonctionnalité                                            | Remarque                                                                     |
|----|-----------------------------------------------------------|------------------------------------------------------------------------------|
|  1 | Authentification des utilisateurs (inscription/connexion) | Utiliser l'authentification JWT pour authentifier les utilisateurs.          |
|  2 | Les utilisateurs doivent avoir accès aux actions basiques<br>de type CRUD sur des projets.  | Un projet peut être défini comme une entité ayant plusieurs collaborateurs<br>(utilisateurs), et chaque projet peut contenir plusieurs problèmes.|
|  3 | Chaque projet peut se voir associer des problèmes qui lui sont liés ; l'utilisateur ne doit pouvoir appliquer le processus CRUD aux problèmes du projet que si il ou elle figure sur la liste des contributeurs. | Un projet ne doit être accessible qu'à son responsable et aux contributeurs.Seuls les contributeurs sont autorisés à créer ou à consulter les problèmes d'un projet.|
|  4 | Chaque problème doit avoir un titre, une description, un assigné (l’assigné par défaut étant l'auteur lui-même),<br> une priorité (FAIBLE, MOYENNE ou ÉLEVÉE), une balise (BUG, AMÉLIORATION ou TÂCHE), un statut (À faire, En cours ou Terminé), le project_id auquel il est lié et un created_time (horodatage), ainsi que d'autres attributs mentionnés dans le diagramme de classe.  | Seuls les contributeurs peuvent créer (Create) et lire (Read)les commentaires relatifs à un problème. En outre, ils ne peuvent les actualiser (Update) et les supprimer (Delete) que s'ils en sont les auteurs.| 
|  5 | Les problèmes peuvent faire l'objet de commentaires de la part des contributeurs au projet auquel ces problèmes appartiennent. Chaque commentaire doit être assorti d'une description, d'un author_user_id, d'un issue_id, et d'un comment_id.| Un commentaire doit être visible par tous les contributeurs du projet, mais il ne peut être actualisé ou supprimé que par son auteur. |
|  6 | Il est interdit à tout utilisateur autorisé autre que l'auteur d'émettre des requêtes d'actualisation et de suppression d'un problème/projet/commentaire.| Autorisation d'actualisation et de suppression.|
    
### Exigences
      Présenter tous les types de points de terminaison différents (code HTTP) à l'aide de Postman ou d'un autre outil de votre choix.
      Expliquer rapidement votre code et en quoi il respecte les normes OWASP et RGPD.
      Présenter la documentation de l'API REST.

### Compétences évaluées
      - Créer une API RESTful avec Django REST
      - Sécuriser une API afin qu'elle respecte les normes OWASP et RGPD
      - Documenter une application
      
---

## Comment utiliser le projet ?
1. Clone the repository

      `git clone https://github.com/memphis-tools/oc_projet10_rest_framework.git`

      `cd oc_projet10_rest_framework`

2. Setup a virtualenv

      `python -m venv env`

      `source env/bin/activate`

      `pip install -U pip`

      `pip install -r requirements.txt`
      
3. Start the application from scratch, run successively

      `python ./manage.py makemigrations`

      `python ./manage.py migrate`

      `python ./manage.py createsuperuser` (and follow instructions)

      `python ./manage.py runserver`

5. Populate a development dummy database and then run the application

   Notice the 3 dummy users username: donald.duck, daisy.duck, loulou.duck. Default password is: applepie94 

      `python ./manage.py init_app_softdesk`

      `python ./manage.py runserver`

7. Read the postman [API documentation](https://documenter.getpostman.com/view/24090419/2s93sc4sWt)

      `Illustration`
![Screenshot](oc_projet10_postman_doc.png)

      `All run in a dvelopment environment`
![Screenshot](oc_projet10_postman_env_development.png)



