



from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views


urlpatterns = [

    path(r'', view=views.TowerListView.as_view(), name='tower_list'),
    path(r'geojson/', view=views.geojson, name='towers_geojson'),
    path(r'buttons/', view=views.TowerButtonListView.as_view(), name='tower_button_list'),
    path(r'districts/', view=views.DistrictListView.as_view(), name='district_list'),
    path(r'map/', view=views.MapView.as_view(), name='towers_map'),

    path(r'district/<str:district>/', view=views.SingleDistrictListView.as_view(), name='single_district_list'),
    path(r'district/<str:district>/map/', view=views.MapView.as_view(), name='district_map'),
    path(r'district/<str:district>/json/', view=views.geojson, name='district_geojson'),

    path(r'bells/', view=views.BellsListView.as_view(), name='bells_list'),
    path(r'unbells/', view=views.UnBellsListView.as_view(), name='un_bells_list'),
    path(r'night/', view=views.PracticeNightListView.as_view(), name='practice_night_list'),

    path(r'tower/<int:pk>/', view=views.TowerDetailView.as_view(), name='tower_detail'),
    path(r'tower/<int:towerid>/json/', view=views.geojson, name='tower_geojson'),
    path(r'tower/<int:towerid>/map/', view=views.MapView.as_view(), name='tower_map'),

    path(r'towers.csv', view=views.tower_csv, name='towers_csv'),
    path(r'contacts.csv', view=views.contact_csv, name='contacts_csv'),
    path(r'websites.csv', view=views.website_csv, name='websites_csv'),
    path(r'photos.csv', view=views.photo_csv, name='photos_csv'),

]