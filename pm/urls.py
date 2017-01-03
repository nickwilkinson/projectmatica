from django.conf.urls import url
from . import views

urlpatterns = [
	url(r'^$', views.project_list, name='project_list'),
	url(r'^project/(?P<pid>\d+)/new/$', views.project_new, name='project_new'),
	url(r'^project/(?P<pid>\d+)/edit/$', views.project_edit, name='project_edit'),
]