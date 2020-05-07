from . import views
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import manage_items, manage_item

api_patterns = [
path('portfolio/', manage_items, name="items"),
path('portfolio/<slug:key>', manage_item, name="single_item")
]
format_suffix_patterns(api_patterns)

urlpatterns = [
    path(r'', views.update_stock_table, name='update_stock_table'),
    path(r'stocks', views.update_stock_table, name='update_stock_table'),
]

urlpatterns += api_patterns