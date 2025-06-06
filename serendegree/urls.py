"""
URL configuration for serendegree project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from core.views import HomeView, UploadScheduleView, AboutView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('upload/', UploadScheduleView.as_view(), name='upload_schedule'),
    path('about/', AboutView.as_view(), name='about'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/docs/', include_docs_urls(title='Serendegree API')),
]
