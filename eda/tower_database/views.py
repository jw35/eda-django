from django.db import models
from django.db.models.fields import Field
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView

from geojson import Point, Feature, FeatureCollection, dump

from .models import Tower, Contact, Website, Photo

# Create your views here.

class TowerListView(ListView):
    model = Tower

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'All towers'
        return context

class DistrictListView(ListView):
    model = Tower
    ordering = ('district', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers by district'
        context["group_by"] = 'district'
        return context


class SingleDistrictListView(ListView):

    def get_queryset(self):
        district = self.kwargs["d"]
        table = {}
        for key, name in Tower.Districts.choices:
            table[name.lower()] = key
        if district not in table:
            raise Http404("Unrecognised District")
        return Tower.objects.filter(district=table[district]).order_by('place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f'Towers in the {self.kwargs["d"].capitalize()} District'
        return context


class BellsListView(ListView):
    queryset = Tower.objects.exclude(ringing_status = 'N').exclude(bells=None)
    ordering = ('-bells', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers rung full-circle, by number of bells'
        context["group_by"] = 'bells'
        return context


class UnBellsListView(ListView):
    queryset = Tower.objects.filter(ringing_status = 'N').exclude(bells=None)
    ordering = ('-bells', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers not rung full-circle, by number of bells'
        context["group_by"] = 'bells'
        context["notes"] = ("Towers may not be rung full-circle because the bells are unringable or derelict, "
                           "hung for chiming only, because the tower is unsafe, etc.")
        return context


class PracticeNightListView(ListView):
    queryset = Tower.objects.exclude(practice_day = '')
    ordering = ('practice_day', 'place', 'dedication')
    template_name = 'tower_database/practice_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers by practice night'
        return context


class TowerDetailView(DetailView):
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


def tower_as_geojson(tower):

    point = Point((float(tower.lng), float(tower.lat)))

    properties = {}

    # All (most) individual Tower fields
    for  field in Tower._meta.get_fields():
        if  isinstance(field, Field) and field.name not in ('id', 'latlng', 'maintainer_notes'):
            properties[field.name] = getattr(tower, field.name)
        # OS Grid isn't actually a field...
        properties['os_grid'] = tower.os_grid

    # Tower primary contact, if available and publishable
    primary_c = {}
    if tower.primary_contact and tower.primary_contact.publish:
        for  field in Contact._meta.get_fields():
            if  isinstance(field, Field) and not isinstance(field, models.ForeignKey):
                primary_c[field.name] = getattr(tower.primary_contact, field.name)
    properties['primary_contact'] = primary_c

    # All other Tower contacts, if publishable
    other_contacts = []
    for contact in tower.other_contacts:
        if contact.publish:
            c = {}
            for  field in Contact._meta.get_fields():
                if  isinstance(field, Field) and not isinstance(field, models.ForeignKey):
                    c[field.name] = getattr(contact, field.name)
            other_contacts.append(c)
    properties['other_contacts'] = other_contacts

    # All websites
    websites = []
    for website in tower.website_set.all():
        w = {}
        for  field in Website._meta.get_fields():
            if  isinstance(field, Field) and not isinstance(field, models.ForeignKey):
                w[field.name] = getattr(website, field.name)
        websites.append(w)
    properties['websites'] = websites

    # All photos
    photos = []
    for photo in tower.photo_set.all():
        p = {}
        for  field in Photo._meta.get_fields():
            if isinstance(field, models.ImageField):
                p[field.name] = getattr(photo, field.name).url
            elif  isinstance(field, Field) and not isinstance(field, models.ForeignKey):
                p[field.name] = getattr(photo, field.name)
        photos.append(p)
    properties['photos'] = photos

    return Feature(id=tower.id, geometry=point, properties=properties)


def geojson(request, pk=None):

    if pk:
        tower = get_object_or_404(Tower, pk=pk)
        result = tower_as_geojson(tower)
        filename = f'tower-{pk}.geojson'

    else:
        features = []
        for tower in Tower.objects.prefetch_related('contact_set', 'website_set', 'photo_set'):
            features.append(tower_as_geojson(tower))
        result = FeatureCollection(features)
        filename = 'towers.geojson'

    response = HttpResponse(
        content_type='application/geo+json',
        #headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )

    dump(result, response)

    return response

