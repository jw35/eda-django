from django.core.management.base import BaseCommand, CommandError

from tower_database.models import Tower, Contact, Dove
import re

from unidecode import unidecode
from urllib.parse import urlparse

class Command(BaseCommand):
    help = 'Compare the database against the copy of Dove'

    def add_arguments(self, parser):

        parser.add_argument("--all-names", action="store_true", help="Print all tower names")
        parser.add_argument("--omit", action="append", metavar='TEST', help="Omit this test")
        parser.add_argument("--only", action="append", metavar='TEST', help="Only perform this test")


    def handle(self, *args, **options):


        def do_this(test):
            return not ( (options["omit"] and test in options["omit"]) or (options["only"] and test not in options["only"]) )

        def is_eq(eda, dove):
            return str(eda) == str(dove)

        def is_county_eq(eda, dove):
            return eda == dove[0]

        def is_dedication_eq(eda, dove):

            # Convert to Dove style

            eda = unidecode(eda)

            eda_subs = (

                (r'\bthe Great\b',                  'Gt'),
                (r'\bMary Magdalene\b',             'Mary Magd'),
                (r'\bMary the Virgin\b',            'Mary V'),
                (r'\bMary the Blessed Virgin\b',    'Mary BV'),
                (r'\bthe Baptist\b',                'Bapt'),
                (r'\bthe Evangelist\b',             'Ev'),
                (r'\bof the Blessed Virgin Mary\b', 'of BVM'),
                (r' and the Holy Host of Heaven\b', ''),
                (r'\bCathedral Church\b',           'Cath Ch'),
                (r'\bthe English Martyrs\b',        'Eng Martyrs'),
                (r'\bKing and Martyr\b',            'K&M'),
                (r'\bof the Holy and Undivided\b',  'of Holy and Undivided'),
                (r'^The ',                          ''),
                (r'\bSt\b',                         'S'),
                (r'\band\b',                        '&'),

            )

            for sub in eda_subs:
                pattern, replacement = sub
                eda = re.sub(pattern, replacement, eda)

            #print(f"'{eda}' '{dove}'")

            return eda == dove

        def is_status_believable(eda, dove):
            if dove != '':
                return eda == 'N'
            return True

        def is_type_eq(eda, dove):

            if eda == '' and dove == 'Full-circle ring':
                return True
            return eda == dove

        def is_bool_eq(eda, dove):
            return (dove != '')  == eda

        def web_page_eq(eda, dove):
            eda_parsed = urlparse(eda)
            dove_parsed = urlparse(dove)
            if eda_parsed.hostname == 'dove.cccbr.org.uk':
                return True
            return (eda_parsed.netloc == dove_parsed.netloc and
                    eda_parsed.path == dove_parsed.path and
                    eda_parsed.query == dove_parsed.query)

        tests = (
            ( 'TowerID', 'dove_towerid', 'towerid', is_eq ),
            ( 'Place', 'place', 'place', is_eq ),
            ( 'County', 'county', 'county', is_county_eq ),
            ( 'Dedication', 'dedication', 'dedicn', is_dedication_eq ),
            ( 'Status', 'ringing_status', 'ur', is_status_believable),
            ( 'Bells', 'bells', 'bells', is_eq ),
            ( 'Type', 'ring_type', 'ringtype', is_type_eq ),
            # Weight
            #( 'Note', 'eda.Note', 'dove.Note', is_eq ),
            ( 'GF' , 'gf', 'gf', is_bool_eq ),
            ( 'OSGrid', 'os_grid', 'ng', is_eq ),
            ( 'Postcode', 'postcode', 'postcode', is_eq ),
            # LAt
            # Lng
            #( 'Website', 'eda.Website', 'dove.WebPage', web_page_eq ),
            ( 'TowerbaseID', 'towerbase_id', 'towerbase', is_eq )
            )




        for tower in Tower.objects.all():

            errors = []

            try:
                dove_tower = Dove.objects.get(ringid=tower.dove_ringid)
            except Dove.DoesNotExist:
                errors.append(f"[RingID] '{dove.ring_id}' not found")
            else:

                for t in tests:
                    (label, us, them, fn) = t
                    if do_this(label):
                      if not fn(getattr(tower,us), getattr(dove_tower,them)):
                        errors.append(f"[{label}] us: '{getattr(tower, us)}', them: '{getattr(dove_tower, them)}'")

                if do_this('Diocese'):
                    if 'Ely' not in dove_tower.diocese.split(';'):
                        errors.append(f"[Diocese] 'Ely' not fonud in Dove Diocese '{dove_tower.diocese}'")

                # Dove normally only list Affiliation for Bells >= 4 and it only matters for
                # Full-circle rings
                if do_this('Affiliation'):
                    if (int(dove_tower.bells) >= 4 and
                        dove_tower.ringtype == 'Full-circle ring' and
                        'Ely Diocesan Association' not in dove_tower.affiliations.split(';')):
                        errors.append(f"[Affiliation] 'Ely Diocesan Association' not found in Dove Affiliations :'{dove_tower.affiliations}'")






            if errors or options["all_names"]:
                self.stdout.write(f"\n{tower.place} {tower.dedication}:")

            if errors:
                for error in errors:
                    self.stdout.write(f"    {error}")

