"""
URL configuration for fastora project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from .views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',indexfile, name='indexfile'),
    path('beauty/',beauty, name='beauty'),
    path('electronics/',electronics, name='electronics'),
    path('gifting/',gifting, name='gifting'),
    path('kids/',kids, name='kids'),
    path('pharmacy/',pharmacy, name='pharmacy'),
    path('meat/',meat, name='meat'),
    path('fruits/', fruits,name='fruits'),
    path('Grocery/',Grocery, name='Grocery'),
    path('profile/', profile, name='profile'),
    path('search/', search, name='search'),
]
