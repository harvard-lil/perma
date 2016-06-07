from django.conf.urls import url
import views

urlpatterns = [
    url(r'^archive/?$', views.monitor_archive, name='monitor_archive'),
]