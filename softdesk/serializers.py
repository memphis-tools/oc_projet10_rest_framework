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
        if value not in ["back-end", "front-end", "iOS", "Android"]:
            raise serializers.ValidationError(
                f"Type '{value}' unknow. Authorized values: back-end, front-end, iOS, Android")
        return value


class ProjectListSerializer(ProjectsSerializerMixin, serializers.ModelSerializer):

    class Meta:
        model = Projects
        fields = ["id", "title", "type", "status"]


class ProjectDetailSerializer(ProjectsSerializerMixin, serializers.ModelSerializer):
    project_users = serializers.SerializerMethodField()

    class Meta:
        model = Projects
        fields = ["id", "title", "description", "type", "status", "project_users"]
        extra_kwargs = {'project_users': {'write_only': True}}

    def get_project_users(self, instance):
        project_users = instance.project_users.all()
        project_queryset = Contributors.objects.filter(user_id__in=project_users).filter(project_id=instance.id)
        serializer = ContributorListSerializer(project_queryset, many=True)
        return serializer.data

    def validate_status(self, instance):
        if instance not in ["Ouvert", "Archivé", "Annulé"]:
            raise serializers.ValidationError(
                f"Project status {instance} unknow. Authorized values: Ouvert, Archivé, Annulé"
            )
        return instance


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
            "general_cnil_approvment",
            "can_be_contacted",
            "can_data_be_shared",
            "can_contribute_to_a_project",
            "can_profile_viewable"
        ]
        extra_kwargs = {'password': {'write_only': True}, 'has_parental_approvement': {'write_only': True}}

    def has_parental_approvement(self, instance):
        """
        Description:
        This is a To-Do feature which may requires an external capability.
        You have to fix our own "parental approvement" mecanism.
        Method should be use inside the validate function below within the UserProtectByRGPD exception.
        By default, because of a Development Environment we set the call back function to True.
        By default, we just ask for a'has_parental_approvement' to True for a minor user.
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
            if 'has_parental_approvement' not in instance:
                raise serializers.ValidationError(
                    ("You are not {settings.RGPD_MIN_AGE} years old, and without parental approvement."
                        "You can not validate CNIL approvement by yourself."
                        "Set a 'has_parental_approvement' attribute to 'True'")
                )
            elif 'has_parental_approvement' in instance and instance['has_parental_approvement'] is False:
                raise serializers.ValidationError(
                    ("You are not {settings.RGPD_MIN_AGE} years old, and without parental approvement."
                        "You can not validate CNIL approvement by yourself."
                        "Set a 'has_parental_approvement' attribute to 'True'")
                )
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


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "birthdate",
            "email",
            "can_be_contacted",
            "can_data_be_shared",
            "can_contribute_to_a_project",
            "can_profile_viewable",
            "created_time"
        ]


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "first_name", "last_name", "email"]


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


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "can_be_contacted",
            "can_data_be_shared",
            "can_contribute_to_a_project",
            "can_profile_viewable"
        ]

    def validate_first_name(self, instance):
        if not len(instance) > 0:
            raise serializers.ValidationError({"first_name": "Can not be null"})
        return instance

    def validate_last_name(self, instance):
        if not len(instance) > 0:
            raise serializers.ValidationError({"last_name": "Can not be null"})
        return instance

    def validate_email(self, instance):
        user = get_user_model().objects.filter(email=instance)
        if user:
            raise serializers.ValidationError({"email": "Email already exists"})
        return instance

    def validate_can_be_contacted(self, instance):
        if instance is not True and instance is not False:
            raise serializers.ValidationError({"can_be_contacted": "True/False expected"})
        return instance

    def validate_can_data_be_shared(self, instance):
        if instance is not True and instance is not False:
            raise serializers.ValidationError({"can_data_be_shared": "True/False expected"})
        return instance

    def validate_can_contribute_to_a_project(self, instance):
        if instance is not True and instance is not False:
            raise serializers.ValidationError({"can_contribute_to_a_project": "True/False expected"})
        return instance

    def validate_can_profile_viewable(self, instance):
        if instance is not True and instance is not False:
            raise serializers.ValidationError({"can_profile_viewable": "True/False expected"})
        return instance


class IssueMixin:
    def validate_balise(self, value):
        if value not in ["BUG", "TASK", "FEATURE"]:
            raise serializers.ValidationError(
                f"Balise '{value}' unknow. Authorized values: BUG, TASK, FEATURE")
        return value

    def validate_priority(self, value):
        if value not in ["LOW", "MEDIUM", "HIGH"]:
            raise serializers.ValidationError(
                f"Priority '{value}' unknow. Authorized values: LOW, MEDIUM, HIGH")
        return value

    def validate_status(self, value):
        if value not in ["To Do", "In Progress", "Finished", "Canceled"]:
            raise serializers.ValidationError(
                f"Status '{value}' unknow. Authorized values: To Do, In Progress, Finished or Canceled")
        return value


class IssueSerializer(IssueMixin, serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = ["title", "description", "status", "balise", "priority", "assignee_user_id"]


class IssuesSerializer(IssueMixin, serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = "__all__"


class IssuesStatusSerializer(IssueMixin, serializers.ModelSerializer):
    class Meta:
        model = Issues
        fields = ["status"]


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
