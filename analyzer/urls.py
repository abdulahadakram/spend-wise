from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/upload/', views.upload_statement, name='upload_statement'),
    path('api/analysis/<str:session_id>/', views.get_analysis, name='get_analysis'),
] 