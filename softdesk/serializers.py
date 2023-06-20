from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from softdesk.models import Projects, Issues, Comments, Contributors


class ProjectsSerializerMixin:
    def validate_type(self, value):
        # type possible: back-end, front-end, iOS ou Android
        if value not in ["back-end", "front-end", "iOS", "Android"]:
            raise serializers.ValidationError(
                f"Type '{value}' unknow. Authorized values: back-end, front-end, iOS, Android")
        return value


class ProjectListSerializer(ProjectsSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Projects
        fields = ["id", "title", "type"]


class ProjectDetailSerializer(ProjectsSerializerMixin, serializers.ModelSerializer):
    project_users = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = ["id", "title", "description", "type", "project_users"]
        extra_kwargs = {'project_users': {'write_only': True}}

    def validate_type(self, value):
        # type possible: back-end, front-end, iOS ou Android
        if value not in ["back-end", "front-end", "iOS", "Android"]:
            raise serializers.ValidationError(
                f"Type '{value}' unknow. Authorized values: back-end, front-end, iOS, Android")
        return value

    def get_project_users(self, instance):
        project_users = instance.project_users.all()
        project_queryset = Contributors.objects.filter(user_id__in=project_users).filter(project_id=instance.id)
        serializer = ContributorListSerializer(project_queryset, many=True)
        return serializer.data


class ContributorListSerializer(serializers.ModelSerializer):
    permission = serializers.SerializerMethodField()

    class Meta:
        model = Contributors
        fields = "__all__"

    def get_permission(self, obj):
        return obj.get_permission_display()


class ContributorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contributors
        fields = "__all__"

    def validate_permission(self, value):
        if value not in {Contributors.AUTHOR, Contributors.CONTRIBUTOR}:
            raise serializers.ValidationError(
                f"Permission {value} unknow. Authorized values: \
                    {Contributors.AUTHOR}, {Contributors.CONTRIBUTOR}"
            )
        return value

    def validate_role(self, value):
        # roles possibles: admin, responsable projet, contributeur projet, auteur commentaire
        if value not in ["admin", "responsable projet", "contributeur projet", "auteur commentaire"]:
            raise serializers.ValidationError(
                f"Role '{value}' unknow. Authorized values: \
                admin, responsable projet, contributeur projet, auteur commentaire")
        return value


class RegisterUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=get_user_model().objects.all())]
    )
    password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "last_name", "email", "password", "password2"]
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, instance):
        if instance['password'] != instance['password2']:
            raise serializers.ValidationError("Passwords must match")
        return instance

    def create(self, data):
        password2 = data.pop('password2')
        user = get_user_model()(**data)
        user.set_password(data['password'])
        user.save()
        return user

    def get(self, request, *args, **kwargs):
        user = get_user_model().objects.all()
        return user


class UserUpdatePasswordSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(required=True, write_only=True)
    password = serializers.CharField(required=True, write_only=False, validators=[validate_password])
    password2 = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = get_user_model()
        fields = ["old_password", "password", "password2"]

    def validate(self, instance):
        if instance['password'] != instance['password2']:
            raise serializers.ValidationError("Passwords must match")

        does_user_update_his_own_pwd = bool(self.context['request'].user.id != self.instance.id)
        is_user_superadmin = bool(self.context['request'].user.is_superuser)
        if bool(does_user_update_his_own_pwd or is_user_superadmin):
            raise serializers.ValidationError("User can only change his password")

        return instance

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError({"old_password": "Old password is not correct"})
        return value


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "email", "password"]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "password"]


class IssueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = "__all__"

    def validate_tag(self, value):
        # tags possibles: bug, tâche, amélioration
        if value not in ["bug", "tâche", "amélioration"]:
            raise serializers.ValidationError(
                f"Tag '{value}' unknow. Authorized values: bug, tâche, amélioration")
        return value

    def validate_priority(self, value):
        # priorité possible: faible, moyenne, élevée
        if value not in ["faible", "moyenne", "élevée"]:
            raise serializers.ValidationError(
                f"Priority '{value}' unknow. Authorized values: faible, moyenne, élevée")
        return value

    def validate_status(self, value):
        # status possibles: à faire, en cours ou terminé
        if value not in ["à faire", "en cours", "terminé"]:
            raise serializers.ValidationError(
                f"Status '{value}' unknow. Authorized values: à faire, en cours, terminé")
        return value


class CommentMixin:
    def validate_title(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Title is mandatory")
        return value

    def validate_description(self, value):
        if len(value) == 0:
            raise serializers.ValidationError("Description is mandatory")
        return value


class CommentListSerializer(CommentMixin, serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ["id", "title", "author_user_id", "issue_id", "created_time"]


class CommentDetailSerializer(CommentMixin, serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ["id", "title", "description", "author_user_id", "issue_id", "created_time"]
