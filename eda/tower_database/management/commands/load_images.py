from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from simple_history.utils import update_change_reason

from tower_database.models import Tower, Photo

import requests
import re
import os

from os.path import isfile

from urllib.request import urlretrieve
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Load tower photos from files'

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):

        Photo.objects.all().delete()

        # reset AUTOINCREMENT counters
        with connection.cursor() as cursor:
            cursor.execute("delete from sqlite_sequence where name='tower_database_photo';")

        for f in os.listdir("../tower_images"):



            if isfile("../tower_images/" + f):

                print(f)

                match = re.match(r'(\d+)-', f)
                if match:

                    print("Got match")

                    tower = Tower.objects.get(pk=match.group(1))

                    photo = tower.photo_set.create()
                    photo.image.save(
                        f,
                        File(open("../tower_images/" + f, 'rb'))
                    )
                    photo.save()

                    update_change_reason(photo, "Image import from websites")
