



from django.urls import path, re_path

from . import views


urlpatterns = [

    path(r'', view=views.towers, name='towers'),
    path(r'tower/<int:tower_id>/', view=views.tower, name='tower'),

]