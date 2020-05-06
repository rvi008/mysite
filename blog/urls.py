from . import views
from django.urls import path

urlpatterns = [
    path('',views.accueil, name='accueil'),
    path('about', views.about, name='about'),
    path('blog/', views.PostList.as_view(), name='home'),
    path('blog/<slug:slug>/', views.PostDetail.as_view(), name='post_detail')
]