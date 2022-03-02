from django.urls import path, include

urlpatterns = []

try:
    urlpatterns.append(
        path('custom/', include('custom_view.api_v2.urls'))
    )
except ImportError:
    pass
