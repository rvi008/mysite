from . import views
from django.urls import path

urlpatterns = [
    path(r'', views.update_stock_table, name='update_stock_table'),
    path(r'stocks', views.update_stock_table, name='update_stock_table'),
    path(r'crowdfunding', views.crowdfunding, name='crowdfunding')
]