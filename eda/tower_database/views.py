from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView

from .models import Tower

# Create your views here.

class TowerListView(ListView):
    model = Tower

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'All towers'
        return context

class TowerListComplexView(ListView):
    model = Tower
    template_name = 'tower_database/tower_list_complex.html'

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
        context["split_by"] = 'district'
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
        context["split_by"] = 'bells'
        return context


class UnBellsListView(ListView):
    queryset = Tower.objects.filter(ringing_status = 'N').exclude(bells=None)
    ordering = ('-bells', 'place', 'dedication')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = 'Towers not rung full-circle, by number of bells'
        context["split_by"] = 'bells'
        context["notes"] = ("Towers may not be rung full-circle because the bells are unringable or derelict, "
                           "hung for chiming only, becasue the tower is unsafe, etc.")
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
