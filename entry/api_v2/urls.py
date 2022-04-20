from django.urls import path
from django.conf.urls import url

from . import views

urlpatterns = [
    # path('entries/<int:entity_id>', views.entryAPI.as_view({'get': 'list'})),
    path('', views.EntryAPI.as_view({
        'post': 'create',
    })),
    path('<int:pk>/', views.EntryAPI.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy',
    })),
    url(r'^search$', views.searchAPI.as_view({'get': 'list'}))
]
