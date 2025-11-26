from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

import re
import os

from os.path import isfile

from simple_history.utils import update_change_reason

from tower_database.models import Tower, Photo

CACHE_DIR = "../tower_images"

class Command(BaseCommand):
    help = 'Load tower photos from files'

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):

        Photo.objects.all().delete()

        # reset AUTOINCREMENT counters
        with connection.cursor() as cursor:
            cursor.execute("delete from sqlite_sequence where name='tower_database_photo';")

        for f in [f for f in os.listdir(CACHE_DIR) if isfile(os.path.join(CACHE_DIR, f))]:

            match = re.match(r'(\d+)-', f)
            if match:

                print(f"Processing {f}")

                tower = Tower.objects.get(pk=match.group(1))

                photo = tower.photo_set.create()
                photo.image.save(
                    f,
                    File(open(os.path.join(CACHE_DIR, f), 'rb'))
                )
                photo.save()

                update_change_reason(photo, "Image import from websites")

            else:
                print(f"Ignoring {f}")
