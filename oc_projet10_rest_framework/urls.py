from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from softdesk.views import ProjectsAPIView, \
    UserRegisterGenericsAPIView, UsersAPIView, UserAPIView, UserUpdatePasswordGenericsAPIView, \
    ProjectsUsersAPIView, IssuesAPIView, IssuesRetrieveUpdateAPIView, CommentsAPIView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', UserRegisterGenericsAPIView.as_view(), name='signup'),
    path('users/', UsersAPIView.as_view(), name='users'),
    path('users/<int:pk>/', UserAPIView.as_view(), name='users_detail'),
    path('users/<int:pk>/change_password/', UserUpdatePasswordGenericsAPIView.as_view(), name='change_password'),
    path('projects/', ProjectsAPIView.as_view(), name='projects'),
    path('projects/<int:pk>/', ProjectsAPIView.as_view(), name='projects_detail'),
    path('projects/<int:pk>/users/', ProjectsUsersAPIView.as_view(), name='users'),
    path('projects/<int:pk>/users/<int:user_id>/', ProjectsUsersAPIView.as_view(), name='users_detail'),
    path('projects/<int:pk>/issues/', IssuesAPIView.as_view(), name='issues'),
    path('projects/<int:pk>/issues/<int:issue_id>/', IssuesAPIView.as_view(), name='issues_detail'),
    path(
        'projects/<int:pk>/issues/<int:issue_id>/change_status/',
        IssuesRetrieveUpdateAPIView.as_view(),
        name='issues_status'),
    path(
        'projects/<int:pk>/issues/<int:issue_id>/comments/',
        CommentsAPIView.as_view(),
        name='comments'
    ),
    path(
        'projects/<int:pk>/issues/<int:issue_id>/comments/<int:comment_id>/',
        CommentsAPIView.as_view(),
        name='comments_detail'
    ),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
