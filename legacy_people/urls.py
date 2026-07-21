from django.urls import path
from . import views

app_name = 'legacy_people'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('form/', views.main_form, name='main_form'),
]
