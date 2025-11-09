from django.shortcuts import render, redirect, get_object_or_404

from .models import Tower

# Create your views here.

def towers(request):

    """
    All towers
    """

    towers = Tower.objects.all()

    return render(request, "tower_database/towers.html",
        context={'towers': towers,
                })


def tower(request, tower_id):

    """
    Individual tower details
    """

    tower = get_object_or_404(Tower, pk=tower_id)

    return render(request, "tower_database/tower.html",
        context={'tower': tower,
                })
