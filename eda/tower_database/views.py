from django.db import models
from django.db.models.fields import Field
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import TemplateView, ListView, DetailView

from geojson import Point, Feature, FeatureCollection, dump
import csv

from .models import Tower, Contact, Website, Photo

import logging
logger = logging.getLogger(__name__)

# Create your views here.

class XFrameOptionsExemptMixin:
    @xframe_options_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class TowerListView(XFrameOptionsExemptMixin, ListView):
    model = Tower

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'All towers'
        return context

class TowerButtonListView(TowerListView):
    template_name = 'tower_database/tower_list_buttons.html'

class DistrictListView(XFrameOptionsExemptMixin, ListView):
    model = Tower
    ordering = ('district', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers by district'
        context["group_by"] = 'district'
        return context


class SingleDistrictListView(XFrameOptionsExemptMixin, ListView):

    def get_queryset(self):
        district = self.kwargs["district"]
        return Tower.objects.filter(district=district).order_by('place', 'dedication')

    def get_context_data(self, **kwargs):
        district = self.kwargs["district"]
        context = super().get_context_data(**kwargs)
        context["title"] = f'Towers in the {Tower.Districts(district).label} District'
        context["district"] = district
        return context


class BellsListView(XFrameOptionsExemptMixin, ListView):
    queryset = Tower.objects.exclude(ringing_status = 'N').exclude(bells=None)
    ordering = ('-bells', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers rung full-circle, by number of bells'
        context["group_by"] = 'bells'
        return context


class UnBellsListView(XFrameOptionsExemptMixin, ListView):
    queryset = Tower.objects.filter(ringing_status = 'N').exclude(bells=None)
    ordering = ('-bells', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers not rung full-circle, by number of bells'
        context["group_by"] = 'bells'
        context["notes"] = ("Towers may not be rung full-circle because the bells are unringable or derelict, "
                           "hung for chiming only, because the tower is unsafe, etc.")
        return context


class PracticeNightListView(XFrameOptionsExemptMixin, ListView):
    queryset = Tower.objects.exclude(practice_day = '')
    ordering = ('practice_day', 'place', 'dedication')
    template_name = 'tower_database/practice_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers by practice night'
        return context


class TowerDetailView(XFrameOptionsExemptMixin, DetailView):
    model = Tower
    context_object_name = 'tower'

    def get_context_data(self, **kwargs):
        admin_group = f'Tower Database admin { self.object.get_district_display() }'
        context = super().get_context_data(**kwargs)
        context['user_can_edit'] = (
            self.request.user.is_superuser or
            self.request.user.groups.filter(name='Tower Database admin').exists() or
            self.request.user.groups.filter(name=admin_group).exists()
        )

        return context


class MapView(XFrameOptionsExemptMixin, TemplateView):
    template_name = 'tower_database/map.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Build config to pass to the map JavaScript
        map_config = { "static_root": static('tower_database/map') }
        if 'towerid' in context:
            tower = get_object_or_404(Tower, pk=context['towerid'])
            map_config["centre"] = [tower.lat, tower.lng]
            map_config["towerid"] = context['towerid']
            # All towers, so we can optionally display them
            map_config["towers_json"] = reverse('towers_geojson')
        elif 'district' in context:
            map_config["district"] = context['district']
            map_config["towers_json"] = reverse('district_geojson', kwargs={'district': context['district']})
        else:
            map_config["towers_json"] = reverse('towers_geojson')
        context['map_config'] = map_config

        return context


def tower_as_geojson(tower):

    point = Point((float(tower.lng), float(tower.lat)))

    omit = ['id', 'latlng', 'maintainer_notes']
    properties = {}

    # All (most) individual Tower fields
    for  name in [f.name for f in Tower._meta.fields if f.name not in omit]:
        properties[name] = getattr(tower, name)
    # OS Grid and url aren't actually fields...
    properties['os_grid'] = tower.os_grid
    properties['url'] = tower.get_absolute_url()

    # Tower primary contact, if available and publishable
    primary_c = {}
    if tower.primary_contact and tower.primary_contact.publish:
        for  name in [f.name for f in Contact._meta.fields if f.name != 'tower']:
            primary_c[name] = getattr(tower.primary_contact, name)
    properties['primary_contact'] = primary_c

    # All other Tower contacts, if publishable
    other_contacts = []
    for contact in tower.other_contacts:
        if contact.publish:
            c = {}
            for  name  in [f.name for f in Contact._meta.fields if f.name != 'tower']:
                c[name] = getattr(contact, name)
            other_contacts.append(c)
    properties['other_contacts'] = other_contacts

    # All websites
    websites = []
    for website in tower.website_set.all():
        w = {}
        for  name in [f.name for f in Website._meta.fields if f.name != 'tower']:
            w[name] = getattr(website, name)
        websites.append(w)
    properties['websites'] = websites

    # All photos
    photos = []
    for photo in tower.photo_set.all():
        p = {}
        for  name in [f.name for f in Photo._meta.fields if f.name != 'tower']:
            if name == 'image':
                p[name] = getattr(photo, name).url
            else:
                p[name] = getattr(photo, name)
        photos.append(p)
    properties['photos'] = photos

    return Feature(id=tower.id, geometry=point, properties=properties)


def geojson(request, towerid=None, district=None):

    logger.info('Rebuilding the GeoJSONson page')

    if towerid:
        tower = get_object_or_404(Tower, pk=towerid)
        result = tower_as_geojson(tower)

    elif district:
        features = []
        for tower in Tower.objects.filter(district=district).prefetch_related('contact_set', 'website_set', 'photo_set'):
            features.append(tower_as_geojson(tower))
        result = FeatureCollection(features)

    else:
        features = []
        for tower in Tower.objects.prefetch_related('contact_set', 'website_set', 'photo_set'):
            features.append(tower_as_geojson(tower))
        result = FeatureCollection(features)

    response = HttpResponse(
        content_type='application/geo+json',
    )

    dump(result, response)

    return response

def as_csv(model, request, queryset=None):

    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="eda-{model.__name__}.csv"'},
    )
    writer = csv.writer(response)

    fields = [f.name for f in model._meta.fields]
    writer.writerow(fields)

    if not queryset:
        queryset = model.objects.all()

    for row in queryset.values(*fields):
        writer.writerow([row[field] for field in fields])

    return response

def tower_csv(response):
    return as_csv(Tower, response)

def contact_csv(response):
    queryset = Contact.objects.filter(publish=True)
    return as_csv(Contact, response, queryset)

def website_csv(response):
    return as_csv(Website, response)

def photo_csv(response):
    return as_csv(Photo, response)
