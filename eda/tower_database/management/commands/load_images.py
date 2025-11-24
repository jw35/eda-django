from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from simple_history.utils import update_change_reason

from tower_database.models import Website, Photo

import requests
import re
import os

from urllib.request import urlretrieve
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class Command(BaseCommand):
    help = 'Load tower photos from referenced websites'

    def add_arguments(self, parser):
        pass


    def handle(self, *args, **options):

        Photo.objects.all().delete()

        # reset AUTOINCREMENT counters
        with connection.cursor() as cursor:
            cursor.execute("delete from sqlite_sequence where name='tower_database_photo';")

        for site in Website.objects.all():

            image_url = None

            if re.search(r'cambridgeringing\.info', site.website):

                r = requests.get(site.website)
                soup = BeautifulSoup(r.content, 'html.parser')

                # <td width='35%' align='center'><img src='balsham.jpg' alt='Balsham Tower' width='223' height='320'></td></tr>

                image_url = urljoin(site.website, soup.img.get('src'))

            elif re.search(r'huntbells\.org\.uk', site.website):

                r = requests.get(site.website)
                soup = BeautifulSoup(r.content, 'html.parser')

                # <figure class="wp-block-image size-large"><img fetchpriority="high" decoding="async" width="1024" height="576" src="https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1024x576.jpg" alt="" class="wp-image-1397" srcset="https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1024x576.jpg 1024w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-300x169.jpg 300w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-768x432.jpg 768w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1536x864.jpg 1536w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-2048x1152.jpg 2048w, https://huntbells.org.uk/wp-content/uploads/Bluntisham-1-1920x1080.jpg 1920w" sizes="(max-width: 1024px) 100vw, 1024px" /></figure>

                for fig in soup.find_all("figure"):
                    if fig.img:
                        image_url = fig.img.get('src')
                        break

            if image_url:

                print(image_url)

                result = urlretrieve(image_url)
                '''
                photo = Photo()
                photo.tower = site.tower
                photo.photo = result[0]
                photo.save()
                '''

                photo = site.tower.photo_set.create()
                photo.photo.save(
                    os.path.basename(image_url),
                    File(open(result[0], 'rb'))
                )
                photo.save()

                update_change_reason(photo, "Image import from websites")

        '''


        # Clear out all the old stuff
        Tower.objects.all().delete()
        Contact.objects.all().delete()
        ContactPerson.objects.all().delete()
        Website.objects.all().delete()
        Photo.objects.all().delete()

        # reset AUTOINCREMENT counters
        with connection.cursor() as cursor:
            cursor.execute("delete from sqlite_sequence where name='tower_database_tower';")
            cursor.execute("delete from sqlite_sequence where name='tower_database_contact';")
            cursor.execute("delete from sqlite_sequence where name='tower_database_contact_person';")
            cursor.execute("delete from sqlite_sequence where name='tower_database_website';")
            cursor.execute("delete from sqlite_sequence where name='tower_database_photo';")

        # Read the data from a file or direct from the spreadsheet
        if options['file']:
            # REad from the supplied file
            tower_csv = open(options['file'], newline='')
        else:
            # Get the CSV data from the master list
            spreadsheet = '1o1pAHht9B3VapS9FziLOrMQlSTMvxQ_JeoGSjfEA9hU'
            sheet = 'Ely DA towers'
            url = f"https://docs.google.com/spreadsheets/d/{spreadsheet}/gviz/tq"
            payload = {'tqx': 'out:csv', 'sheet': sheet}
            r = requests.get(url, payload)
            tower_csv = StringIO(r.text)

        # Load suitably-transformed data into a dictionary
        for csv_row in csv.DictReader(tower_csv):

            self.stdout.write(csv_row['Place'])

            db_row = {}

            for f, t in easy_fields:
                db_row[t] = csv_row[f]

            for f, t in boolean_fields:
                db_row[t] = csv_row[f] == "Yes"

            for f, t, l in lookup_fields:
                if csv_row[f]:
                    db_row[t] = l[csv_row[f]]

            if csv_row['Week']:
                weeks = re.split(r',? +', csv_row['Week'])
                weeks = [w.lower() for w in weeks]
                db_row['practice_weeks'] = weeks
            else:
                db_row['practice_weeks'] = []

            db_row['bells'] = int(csv_row['Bells'])
            if csv_row['Peals']:
                db_row['peals'] = int(csv_row['Peals'])

            db_row['lat'] = round(float(csv_row['Lat']), 5)
            db_row['lng'] = round(float(csv_row['Lng']), 5)

            db_row['position'] = f"{ round(float(csv_row['Lat']), 5) },{ round(float(csv_row['Lng']), 5) }"

            # Load the dictionary into an instance for the form and validate it
            f = TowerForm(db_row)
            if not f.is_valid():
                if f.errors:
                    for (k, v) in f.errors.as_data().items():
                        for ex in v:
                            for e in ex:
                                print(f'   {k}: {e}')
                if f.non_field_errors():
                    print(f.non_field_errors())
            # ...and if it validates, save it
            else:

                new_row = f.save()
                update_change_reason(new_row, "Initial data load")

                # Add contact(s)

                if csv_row['Secretary'] or csv_row['Phone'] or csv_row['Email']:

                    publish = True
                    if csv_row['Band contact'] and csv_row['Bells contact']:
                        role = Contact.Roles.CONTACT
                    elif csv_row['Band contact']:
                        role = Contact.Roles.BAND_CONTACT
                    elif csv_row['Bells contact']:
                        role = Contact.Roles.BELLS_CONTACT
                    else:
                        role = Contact.Roles.CONTACT
                        publish = False

                    # Make a new ContactPerson and ann them to Contact if we have a name or phone number
                    if csv_row['Secretary'] or csv_row['Phone']:

                        match = re.match(r'((Mr|Mrs|Miss|Revd|Dr) +)?(.+) +(\w+)', csv_row['Secretary'])
                        if match:
                            title = match.group(2) if match.group(2) else ''
                            forename = match.group(3) if match.group(3) else ''
                            name = match.group(4) if match.group(4) else ''
                        else:
                            title = forename = ''
                            name = csv_row['Secretary']

                        (contact_person, created) = ContactPerson.objects.get_or_create(title=title, forename=forename, name=name, personal_phone=csv_row['Phone'], personal_email=csv_row['Email'])
                        if created:
                            update_change_reason(contact_person, "Initial data load")

                        contact = new_row.contact_set.create(role=role, publish=publish, primary=True, person=contact_person)
                        update_change_reason(contact, "Initial data load")

                    # Otherwise, just add a new Contact
                    else:

                        new_row.contact_set.create(role=role, publish=publish, primary=True, email=csv_row['Email'])
                        update_change_reason(contact, "Initial data load")


                # Add website, unless it points to Dove
                if csv_row['Website'] and "dove.cccbr.org.uk" not in csv_row['Website']:
                    website = new_row.website_set.create(website=csv_row['Website'], link_text="District website")
                    update_change_reason(website, "Initial data load")

        '''