from django.urls import path
from . import views

app_name = 'legacy_people'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('form/', views.main_form, name='main_form'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
]
