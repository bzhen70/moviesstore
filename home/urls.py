from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='home.index'),
    path('about', views.about, name='home.about'),
    path('map', views.map, name='home.map'),
    path('api/trending', views.trending_movies_api, name='trending_movies_api'),
]