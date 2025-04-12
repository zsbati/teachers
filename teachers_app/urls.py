from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('change-password/', views.change_password, name='change_password'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]
