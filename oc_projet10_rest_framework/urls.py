from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from softdesk.views import ProjectsAPIView, \
    RegisterUserGenericsAPIView, UserListAPIView, UserAPIView, UserUpdatePasswordGenericsAPIView, \
    ProjectsUserAPIView, ProjectsIssuesAPIView, ProjectsIssuesCommentAPIView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', RegisterUserGenericsAPIView.as_view(), name='signup'),
    path('users/', UserListAPIView.as_view(), name='users'),
    path('users/<int:pk>/', UserAPIView.as_view(), name='users_detail'),
    path('users/<int:pk>/change_password/', UserUpdatePasswordGenericsAPIView.as_view(), name='change_password'),
    path('projects/', ProjectsAPIView.as_view(), name='projects'),
    path('projects/<int:pk>/', ProjectsAPIView.as_view(), name='projects_detail'),
    path('projects/<int:pk>/users/', ProjectsUserAPIView.as_view(), name='users'),
    path('projects/<int:pk>/users/<int:user_id>/', ProjectsUserAPIView.as_view(), name='users_detail'),
    path('projects/<int:pk>/issues/', ProjectsIssuesAPIView.as_view(), name='issues'),
    path('projects/<int:pk>/issues/<int:issue_id>/', ProjectsIssuesAPIView.as_view(), name='issues_detail'),
    path(
        'projects/<int:pk>/issues/<int:issue_id>/comments/',
        ProjectsIssuesCommentAPIView.as_view(),
        name='comments'
    ),
    path(
        'projects/<int:pk>/issues/<int:issue_id>/comments/<int:comment_id>/',
        ProjectsIssuesCommentAPIView.as_view(),
        name='comments_detail'
    ),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
