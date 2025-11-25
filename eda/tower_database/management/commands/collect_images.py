from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from simple_history.utils import update_change_reason

from tower_database.models import Website, Photo

import requests
import re
import os

import shutil

from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Collect tower photos from referenced websites'

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):

        shutil.rmtree("../tower_images")
        os.mkdir("../tower_images")

        for site in Website.objects.all():

            image_url = None

            if re.search(r'cambridgeringing\.info', site.url):

                r = requests.get(site.url)
                soup = BeautifulSoup(r.content, 'html.parser')

                # <td width='35%' align='center'><img src='balsham.jpg' alt='Balsham Tower' width='223' height='320'></td></tr>

                image_url = urljoin(site.url, soup.img.get('src'))

            elif re.search(r'huntbells\.org\.uk', site.url):

                r = requests.get(site.url)
                soup = BeautifulSoup(r.content, 'html.parser')

                # <figure class="wp-block-image size-large"><img fetchpriority="high" decoding="async" width="1024" height="576" src="https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1024x576.jpg" alt="" class="wp-image-1397" srcset="https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1024x576.jpg 1024w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-300x169.jpg 300w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-768x432.jpg 768w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1536x864.jpg 1536w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-2048x1152.jpg 2048w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1920x1080.jpg 1920w" sizes="(max-width: 1024px) 100vw, 1024px" /></figure>

                for fig in soup.find_all("figure"):
                    if fig.img:
                        image_url = fig.img.get('src')
                        break

            if image_url:

                print(image_url)

                path = urlparse(image_url).path
                fname = os.path.basename(path)

                savefile = f"../tower_images/{site.tower.pk}-{fname}"

                print(savefile)

                img_data = requests.get(image_url).content
                with open(savefile, 'wb') as handler:
                    handler.write(img_data)

        print(os.getcwd())
