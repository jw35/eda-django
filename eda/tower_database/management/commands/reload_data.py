from django.core.management.base import BaseCommand, CommandError

from tower_database.models import Tower, Contact, ContactMap
import requests
import csv
import re

from io import StringIO

easy_fields = (
    ('Place', 'place'),
    ('Dedication', 'dedication'),
    ('Full dedication', 'full_dedication'),
    ('Nickname', 'nickname'),
    ('Service', 'service'),
    ('Practice', 'practice'),
    ('Bells', 'bells'),
    ('Weight', 'weight'),
    ('Note', 'note'),
    ('OS grid', 'os_grid'),
    ('Postcode', 'postcode'),
    ('Lng', 'lat'),
    ('Lat', 'lng'),
    ('Dove Tower ID', 'dove_towerid'),
    ('Dove Ring ID', 'dove_ringid'),
    ('TowerBase ID', 'towerbase_id'),
    ('Notes', 'notes'),
    ('Longer notes', 'long_notes'),
    ('Maintainer notes', 'maintainer_notes'),
)

boolean_fields = (
    ('Include dedication', 'include_dedication'),
    ('Report', 'report'),
    ('Check', 'travel_check'),
    ('GF', 'gf'),
)

lookup_fields = (
    ('County', 'county', {'Cambridgeshire': 'C', 'Norfolk': 'N'}),
    ('District', 'district', {'Cambridge': 'C', 'Ely': 'E', 'Huntingdon': 'H', 'Wisbech': 'W'}),
    ('Status', 'ringing_status', {'Regular ringing': 'R', 'Occasional ringing': 'O', 'No ringing': 'N'}),
    ('Day', 'practice_day', {'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed', 'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat', 'Sunday': 'Sun'}),
    ('Type', 'ring_type', {'Full-circle ring': 'Full', 'Lightweight ring': 'Light',
                           'Carillon': 'Carillon', 'Tubular chime': 'T-chime',
                           'Hemispherical chime': 'H-chinme', 'Chime': 'Chime',
                           'Display bells': 'Display', 'Future ring': 'Future',
                           'Other bells': 'Other'}
    ))


class Command(BaseCommand):
    help = 'Reload the database from the master list'

    def add_arguments(self, parser):
        parser.add_argument("--file", help="Import from CSV, rather than collecting directly")


    def handle(self, *args, **options):

        # Clear out all the old stuff
        Tower.objects.all().delete()
        Contact.objects.all().delete()

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

        for csv_row in csv.DictReader(tower_csv):

            self.stdout.write(csv_row['Place'])

            db_row = Tower()

            for f, t in easy_fields:
                setattr(db_row, t, csv_row[f])

            for f, t in boolean_fields:
                setattr(db_row, t, csv_row[f] == "Yes")

            for f, t, l in lookup_fields:
                if csv_row[f]:
                    setattr(db_row, t, l[csv_row[f]])

            weeks = re.split(r', +', csv_row['Week'])
            db_row.practice_weeks = weeks

            db_row.bells = int(csv_row['Bells'])
            if csv_row['Peals']:
                db_row.peals = int(csv_row['Peals'])

            if csv_row['Secretary'] or csv_row['Phone'] or csv_row['Email']:
                (contact, created) = Contact.objects.get_or_create(name=csv_row['Secretary'], phone=csv_row['Phone'], email=csv_row['Email'])
                db_row.primary_contact = contact

            contact_use = ''
            if csv_row['Band contact'] and csv_row['Bells contact']:
                db_row.contact_use = 'All'
            elif csv_row['Band contact']:
                db_row.contact_use = 'Band only'
            elif csv_row['Bells contact']:
                db_row.contact_use = 'Bells only'
            else:
                db_row.contact_use = 'None'

            db_row.save()

            if csv_row['Website']:
                db_row.website_set.create(website=csv_row['Website'])

