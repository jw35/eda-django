



from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views


urlpatterns = [

    path(r'', view=views.TowerListView.as_view(), name='tower_list'),
    path(r'district/', view=views.DistrictListView.as_view(), name='district_list'),
    path(r'district/<str:d>/', view=views.SingleDistrictListView.as_view(), name='single_district_list'),
    path(r'bells/', view=views.BellsListView.as_view(), name='bells_list'),
    path(r'unbells/', view=views.UnBellsListView.as_view(), name='un_bells_list'),
    path(r'night/', view=views.PracticeNightListView.as_view(), name='practice_night_list'),
    path(r'tower/<int:pk>/', view=views.TowerDetailView.as_view(), name='tower_detail'),
    path(r'geojson/', view=views.geojson, name='towers_geojson'),
    path(r'geojson/tower/<int:pk>/', view=views.geojson, name='tower_geojson'),
    path(r'geojson/district/<str:d>/', view=views.geojson, name='district_geojson'),
    path(r'map/', view=TemplateView.as_view(template_name="tower_database/map.html"), name='map'),

]