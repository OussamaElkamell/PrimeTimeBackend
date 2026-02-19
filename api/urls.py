from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

urlpatterns = [
    # Auth
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.ProfileView.as_view(), name='profile'),
    path('auth/profile/settings/', views.ProfileUpdateView.as_view(), name='profile-update'),
    path('auth/delete/', views.DeleteAccountView.as_view(), name='delete-account'),

    # Todos
    path('todos/', views.TodoListCreateView.as_view(), name='todo-list'),
    path('todos/<uuid:pk>/', views.TodoDetailView.as_view(), name='todo-detail'),

    # Sessions
    path('sessions/active/', views.SessionActiveView.as_view(), name='session-active'),
    path('sessions/start/', views.SessionStartView.as_view(), name='session-start'),
    path('sessions/<uuid:pk>/transition/', views.SessionTransitionView.as_view(), name='session-transition'),
    path('sessions/<uuid:pk>/stop/', views.SessionStopView.as_view(), name='session-stop'),

    # History
    path('history/daily/', views.DailyHistoryView.as_view(), name='history-daily'),
    path('history/range/', views.RangeHistoryView.as_view(), name='history-range'),
]
