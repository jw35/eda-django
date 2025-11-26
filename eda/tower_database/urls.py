



from django.urls import path, re_path

from . import views


urlpatterns = [

    path(r'', view=views.TowerListView.as_view(), name='tower_list'),
    path(r'complex', view=views.TowerListComplexView.as_view(), name='tower_list_complex'),
    path(r'district/', view=views.DistrictListView.as_view(), name='district_list'),
    path(r'district/<str:d>/', view=views.SingleDistrictListView.as_view(), name='single_district_list'),
    path(r'bells/', view=views.BellsListView.as_view(), name='bells_list'),
    path(r'unbells/', view=views.UnBellsListView.as_view(), name='un_bells_list'),
    path(r'night/', view=views.PracticeNightListView.as_view(), name='practice_night_list'),
    path(r'tower/<int:pk>/', view=views.TowerDetailView.as_view(), name='tower_detail'),

]