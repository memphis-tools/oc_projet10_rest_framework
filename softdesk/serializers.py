from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from datetime import date

from softdesk.models import Projects, Issues, Comments, Contributors
from softdesk.exceptions import UserProtectByRGPD


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

    # def validate_type(self, value):
    #     # type possible: back-end, front-end, iOS ou Android
    #     if value not in ["back-end", "front-end", "iOS", "Android"]:
    #         raise serializers.ValidationError(
    #             f"Type '{value}' unknow. Authorized values: back-end, front-end, iOS, Android")
    #     return value

    def get_project_users(self, instance):
        project_users = instance.project_users.all()
        project_queryset = Contributors.objects.filter(user_id__in=project_users).filter(project_id=instance.id)
        serializer = ContributorListSerializer(project_queryset, many=True)
        return serializer.data


class ContributorListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Contributors
        fields = "__all__"

    def get_role(self, obj):
        return obj.get_role_display()


class ContributorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contributors
        fields = "__all__"

    def validate_role(self, value):
        if value not in {Contributors.AUTHOR, Contributors.CONTRIBUTOR}:
            raise serializers.ValidationError(
                f"Role {value} unknow. Authorized values: \
                    {Contributors.AUTHOR}, {Contributors.CONTRIBUTOR}"
            )
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
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "birthdate",
            "email",
            "password",
            "password2",
            "has_parental_approvement",
            "can_be_contacted",
            "can_data_be_shared"
        ]
        extra_kwargs = {'password': {'write_only': True}, 'has_parental_approvement': {'write_only': True}}

    def has_parental_approvement(self, instance):
        """
        Description:
        This is a To-Do feature which requires an external capability.
        You have to fix our own "parental approvement" mecanism.
        By default, because of a Development Environment we set the call back function to True.
        """
        return True

    def has_rgpd_min_age(self, birthdate):
        today = date.today()
        y_bday, m_bday, d_bday = [int(item) for item in str(birthdate).split("-")]

        if today.year - y_bday < settings.RGPD_MIN_AGE:
            raise UserProtectByRGPD()
        elif today.year - y_bday == settings.RGPD_MIN_AGE:
            if today.month > m_bday or (today.month == m_bday and today.day > d_bday):
                raise UserProtectByRGPD()
        return birthdate

    def validate(self, instance):
        try:
            if self.has_rgpd_min_age(instance['birthdate']):
                if instance['password'] != instance['password2']:
                    raise serializers.ValidationError("Passwords must match")
                return instance
        except UserProtectByRGPD:
            instance['can_data_be_shared'] = False
            if not self.has_parental_approvement(instance):
                raise serializers.ValidationError(f"You are not {settings.RGPD_MIN_AGE} old, \
                                                    and without parental approvement")
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


class UserUpdateContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["can_be_contacted"]

    def validate_can_data_be_shared(self, instance):
        if instance is not True and instance is not False:
            raise serializers.ValidationError({"can_be_contacted": "True/False expected"})
        return instance


class UserUpdateDataSharingSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["can_data_be_shared"]

    def validate(self, instance):
        if isinstance(instance, bool):
            raise serializers.ValidationError({"can_data_be_shared": "True/False expected"})
        return instance


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "email"]


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "birthdate",
            "email",
            "can_be_contacted",
            "can_data_be_shared",
            "has_parental_approvement"
        ]


class IssueMixin:
    def validate_balise(self, value):
        # balises possibles: bug, tâche, amélioration
        if value not in ["BUG", "TASK", "FEATURE"]:
            raise serializers.ValidationError(
                f"Balise '{value}' unknow. Authorized values: BUG, TASK, FEATURE")
        return value

    def validate_priority(self, value):
        # priorité possible: faible, moyenne, élevée
        if value not in ["LOW", "MEDIUM", "HIGH"]:
            raise serializers.ValidationError(
                f"Priority '{value}' unknow. Authorized values: LOW, MEDIUM, HIGH")
        return value

    def validate_status(self, value):
        # statuts possibles: à faire, en cours ou terminé
        if value not in ["To Do", "In Progress", "Finished"]:
            raise serializers.ValidationError(
                f"Status '{value}' unknow. Authorized values: To Do, In Progress, Finished")
        return value


class IssueSerializer(IssueMixin, serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = ["title", "description", "status", "balise", "priority", "assignee_user_id"]


class IssuesSerializer(IssueMixin, serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = "__all__"


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
        fields = ["id", "uuid", "title", "description", "author_user_id", "issue_id", "created_time"]


class CommentUpdateSerializer(CommentMixin, serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ["title", "description"]
