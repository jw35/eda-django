from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from multiselectfield import MultiSelectField
from simple_history.models import HistoricalRecords

import re

from collections import defaultdict

# Create your models here.

class Contact(models.Model):
    name = models.CharField(max_length=100, blank=True, help_text="Contact name (with or without title), or role")
    phone = models.CharField(max_length=100, blank=True, help_text="Contact phone number")
    phone2 = models.CharField(max_length=100, blank=True, verbose_name="Phone", help_text="Alternate phone number")
    email = models.EmailField(max_length=100, blank=True, help_text="Contact email address")
    history = HistoricalRecords()

    def __str__(self):
        return ' / '.join([f for f in (self.name, self.phone, self.phone2, self.email) if f != ''])

    class Meta:
        ordering = ["name", "email"]
        unique_together = "name", "phone", "phone2", "email"
        constraints = [
            models.CheckConstraint(
                condition=~Q(name='') | ~Q(phone = '') | ~Q(phone2 = '') | ~Q(email=''),
                name="no_non_blank_contacts",
                violation_error_message="Contacts can't be entirely blank"
            ),
        ]

class TowerConstants():

    # Probable times without leading '0''
    BAD_TIME_PATTERN = re.compile(r'\b(?<!\d)\d:\d\d(?!\d)\b')

    # Acceptable weight patterns
    WEIGHT_PATTERN = re.compile(r'\d+½? cwt|\d+-\d+-\d+')

    # Acceptable note patterns (with no Cb or E#)
    NOTE_PATTERN = re.compile(r'([DGA](#|b)?)|([CF]#?)|([EB]b?)')

    # 6 figure NAtional Grid in the Association area
    GRID_PATTERN = re.compile(r'(TL|TF)\d{6}')

    # Acceptable PostCodes (probably overly restrictive)
    POSTCODE_PATTERN = re.compile(r'\w\w\d+ \d\w\w')

    # Match 'check' if not followed by a Bank Holiday reference, 'by arrangement' and 'by invitation'
    CHECK_PATTERN = re.compile(r'\b(check(?! if Bank Holiday)|by arrangement|by invitation)\b', re.IGNORECASE)

    WEEKDAY_PATTERN = re.compile(r'\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)s?\b', re.IGNORECASE)

    # Valid phrases for week patterns
    WEEK_PHRASE_PATTERN = re.compile(r'1st|2nd|3rd|4th|5th')

class Tower(models.Model):

    class Counties(models.TextChoices):
        CAMBRIDGESHIRE = "C"
        NORFOLK = "N"

    class Districts(models.TextChoices):
        CAMBRIDGE = 'C'
        ELY = 'E'
        HUNTINGDON= 'H'
        WISBECH = 'W'

    class RingingStatus(models.TextChoices):
        REGULAR = 'R'
        OCCASIONAL = 'O'
        NONE = 'N'

    class Days(models.TextChoices):
        MONDAY = 'Mon'
        TUESDAY = 'Tue'
        WEDNESDAY = 'Wed'
        THURSDAY = 'Thu'
        FRIDAY = 'Fri'
        SATURDAY = 'Sat'
        SUNDAY = 'Sun'

    class PracticeWeeks(models.TextChoices):
        NOT = 'Not', 'Not'
        W1 = '1st', '1st'
        W2 = '2nd', '2nd'
        W3 = '3rd', '3rd'
        W4 = '4th', '4th'
        W5 = '5th', '5th'
        ALT = 'Alt', 'Alternate'

    class RingTypes(models.TextChoices):
        FULL = 'Full', 'Full-circle ring'
        LIGHT = 'Light', 'Lightweight ring'
        CARILLON = 'Carillon', 'Carillon'
        C_CHIME = 'C-chine', 'Clock chime'
        T_CHIME = 'T-chime', 'Tubular chime'
        H_CHIME = 'H-chinme', 'Hemispherical chime'
        CHIME = 'Chime', 'Chime'
        DISPLAY = 'Display', 'Display bells'
        FUTURE = 'Future', 'Future ring'
        OTHER = 'Other', 'Other bells'


    class ContactUses(models.TextChoices):
        ALL = 'All'
        BELLS_ONLY = 'Bells only'
        BAND_ONLY = 'Band only'
        NONE = 'None'

    def bell_validator(value):
        if value < 3 or value > 12:
            raise ValidationError("Number of bells must be between 3 and 12")

    def time_validator(value):
        if TowerConstants.BAD_TIME_PATTERN.search(value):
            raise ValidationError("Time value missing leading '0'")

    def initial_capital_validator(value):
        if (value[0].isupper() and not
            value.startswith(('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'))):
            raise ValidationError("No initial capital, except for days of week")

    def week_validator(value):
        if (Tower.PracticeWeeks.NOT in value and
            Tower.PracticeWeeks.W1  not in value and
            Tower.PracticeWeeks.W2  not in value and
            Tower.PracticeWeeks.W3  not in value and
            Tower.PracticeWeeks.W4  not in value and
            Tower.PracticeWeeks.W5  not in value):
            raise ValidationError(f"Must have at least one week with 'Not'")
        if ((Tower.PracticeWeeks.NOT in value or
             Tower.PracticeWeeks.W1  in value or
             Tower.PracticeWeeks.W2  in value or
             Tower.PracticeWeeks.W3  in value or
             Tower.PracticeWeeks.W4  in value or
             Tower.PracticeWeeks.W5  in value
           ) and Tower.PracticeWeeks.ALT in value):
            raise ValidationError(f"Can't have both week numbers and 'Alternate'")

    def weight_validator(value):
        if not TowerConstants.WEIGHT_PATTERN.fullmatch(value):
            raise ValidationError(f"Wrong format for weight (use e.g. '2-4-3-4' or '12cwt')")

    def note_validator(value):
        if not TowerConstants.NOTE_PATTERN.fullmatch(value):
            raise ValidationError(f"Wrong format for note (use A-G optionally followed by # or b if appropriate)")

    def grid_validator(value):
        if not TowerConstants.GRID_PATTERN.fullmatch(value):
            raise ValidationError(f"Wrong format for OS grid (use, e.g. TL123456")

    def postcode_validator(value):
        if not TowerConstants.POSTCODE_PATTERN.fullmatch(value):
            raise ValidationError(f"Wrong format for Postcode")

    place = models.CharField(max_length=100, help_text="Town or village containing the tower")
    county  = models.CharField(max_length=100, choices=Counties, default='Cambridgeshire')
    dedication = models.CharField(max_length=100, help_text="Church dedication. Use ‘St’ not ‘St.’; ‘and’ not ‘&’")
    full_dedication = models.CharField(max_length=100, blank=True)
    nickname = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=10, choices=Districts)
    include_dedication = models.BooleanField(default=False, help_text="For places with more than one tower [Cambridge], or for towers in different places that have the same name [Chesterton])")
    ringing_status = models.CharField(max_length=20, blank=True, choices=RingingStatus, help_text="Full-circle ringing status")
    report = models.BooleanField(default=False, verbose_name="In annual report?")
    service = models.CharField(max_length=200, blank=True, validators=[time_validator, initial_capital_validator], help_text="Short description of normal service ringing. No initial capital (unless day of week)")
    practice = models.CharField(max_length=200, blank=True, validators=[time_validator, initial_capital_validator], help_text="Short description of normal practice ringing. No initial capital (unless day of week)")
    practice_day = models.CharField(max_length=9, blank=True, choices=Days, help_text="Day of the week of main practice")
    practice_weeks = MultiSelectField(max_length=50, blank=True, choices=PracticeWeeks, validators=[week_validator], help_text="Week(s) of the month for main practice if not all")
    travel_check = models.BooleanField(default=False, help_text="Check before travelling to practices?")
    bells = models.PositiveIntegerField(null=True, blank=True, help_text="Number of ringable bells",validators=[bell_validator])
    ring_type = models.CharField(max_length=20, blank=True, choices=RingTypes)
    weight =models.CharField(max_length=50, blank=True, validators=[weight_validator], help_text="Use ‘15-3-13’ or ‘6cwt’")
    note = models.CharField(max_length=10, blank=True, validators=[note_validator], help_text="Use A-G optionally followed by '#' or ‘b’")
    gf = models.BooleanField(blank=True, null=True, verbose_name="Ground Floor?")
    os_grid= models.CharField(max_length=8, blank=True, validators=[grid_validator], verbose_name='OS Grid')
    postcode = models.CharField(max_length=10, blank=True, validators=[postcode_validator])
    lat = models.DecimalField(max_digits=5, blank=True, null=True, decimal_places=3)
    lng = models.DecimalField(max_digits=5, blank=True, null=True, decimal_places=3)
    primary_contact = models.ForeignKey(Contact, blank=True, null=True, on_delete=models.PROTECT, related_name="tower_primary_set")
    contact_use = models.CharField(max_length=10, choices=ContactUses, default='All', help_text="Intended use of contact details")
    other_contacts = models.ManyToManyField(Contact, through="ContactMap", related_name="tower_oher_set")
    peals = models.PositiveIntegerField(null=True , blank=True, help_text="Peals in most recent Annual Report")
    dove_towerid = models.CharField(max_length=10, blank=True, verbose_name="Dove TowerID")
    dove_ringid = models.CharField(max_length=10, blank=True, verbose_name="Dove RingID")
    towerbase_id = models.CharField(max_length=10, blank=True, verbose_name="Towerbase ID")
    notes = models.CharField(max_length=100, blank=True, help_text="For display, especially in the Annual Report")
    long_notes = models.TextField(blank=True, help_text="For display when space isn’t at a premium")
    maintainer_notes = models.TextField(blank=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.place}  ({self.dedication})'

    @property
    def dove_link(self):
        return f"https://dove.cccbr.org.uk/tower/{self.dove_towerid}"

    @property
    def bellboard_link(self):
        return f"https://bb.ringingworld.co.uk/search?dove_tower={self.dove_towerid}"

    @property
    def felstead_link(self):
        return f"https://felstead.cccbr.org.uk/tbid.php?tid={self.towerbase_id}"


    def clean(self):

        """
        Make various cross-field checks. Many of these are a bit heuristic.
        """

        errors = defaultdict(list)

        # ringing & saervice/practice
        if self.ringing_status == Tower.RingingStatus.NONE and (self.service or self.practice):
            errors['ringing_status'].append(f"Iinconsistent with Service or Practice")

        # practice_day & practice
        if ((self.get_practice_day_display().lower() not in self.practice.lower()) or
           (TowerConstants.WEEKDAY_PATTERN.search(self.practice) and not self.practice_day)):
            errors['practice_day'].append(f"Inconsistent with Practice")

        # ravel_check & practice
        if TowerConstants.CHECK_PATTERN.search(self.practice) and not self.travel_check:
            errors['travel_check'].append(f"Practice mentions 'check'")
        elif self.travel_check and not TowerConstants.CHECK_PATTERN.search(self.practice):
            errors['travel_check'].append(f"Practice doesn't mention 'check'")

        # practice_weeks & practice
        if not TowerConstants.CHECK_PATTERN.search(self.practice):
            for phrase in TowerConstants.WEEK_PHRASE_PATTERN.findall(self.practice):
                if phrase not in self.practice_weeks:
                    errors['practice_weeks'].append(f"'{phrase}' appears in in Practice")

        for phrase in self.practice_weeks:
            if phrase.lower() not in self.practice.lower():
                errors['practice_weeks'].append(f"'{phrase}' doesn't appear in Practice")


        if errors:
            raise ValidationError(errors)


    class Meta:
        ordering = ["place", "dedication"]
        constraints = [
            models.UniqueConstraint(fields=["place", "dedication"], name="unique_place_dedication",
                violation_error_message="Can't have two towers with the same place and dedication")
        ]


class Website(models.Model):

    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    website = models.URLField()
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.website}  ({self.tower})'

    class Meta:
        ordering = ["website"]


class ContactMap(models.Model):

    class Roles(models.TextChoices):
        OTHER_CONTACT = 'C'
        TOWER_CAPTAI = 'TC'
        RINGING_MASTER = 'RM'
        STEEPLEKEEPER = 'SK'

    role = models.CharField(max_length=30, choices=Roles)
    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    publish = models.BooleanField(default=True)
    history = HistoricalRecords()

    def __str__(self):
        return f'{self.get_role_display()} - {self.tower} - {self.contact}'

    class Meta:
        '''
        # Throws AttributeError: 'list' object has no attribute 'clone' ???
        constraints = [
            models.UniqueConstraint(
                fields=["tower", "contact"], name="unique_person_group"
            )
        ],
        '''
        #unique_together = ['tower', 'contact']
        ordering = ["tower", "role"]

# Auto-generated with ./manage.py inspectdb

class DoveTower(models.Model):
    towerid = models.CharField(db_column='TowerID', blank=True, null=True)  # Field name made lowercase.
    ringid = models.CharField(db_column='RingID', primary_key=True)  # Field name made lowercase.
    ringtype = models.CharField(db_column='RingType', blank=True, null=True)  # Field name made lowercase.
    place = models.CharField(db_column='Place', blank=True, null=True)  # Field name made lowercase.
    place2 = models.CharField(db_column='Place2', blank=True, null=True)  # Field name made lowercase.
    placecl = models.CharField(db_column='PlaceCL', blank=True, null=True)  # Field name made lowercase.
    dedicn = models.CharField(db_column='Dedicn', blank=True, null=True)  # Field name made lowercase.
    towerstatus = models.CharField(db_column='TowerStatus', blank=True, null=True)  # Field name made lowercase.
    statusfirst = models.CharField(db_column='StatusFirst', blank=True, null=True)  # Field name made lowercase.
    barededicn = models.CharField(db_column='BareDedicn', blank=True, null=True)  # Field name made lowercase.
    altname = models.CharField(db_column='AltName', blank=True, null=True)  # Field name made lowercase.
    ringname = models.CharField(db_column='RingName', blank=True, null=True)  # Field name made lowercase.
    region = models.CharField(db_column='Region', blank=True, null=True)  # Field name made lowercase.
    county = models.CharField(db_column='County', blank=True, null=True)  # Field name made lowercase.
    country = models.CharField(db_column='Country', blank=True, null=True)  # Field name made lowercase.
    histregion = models.CharField(db_column='HistRegion', blank=True, null=True)  # Field name made lowercase.
    iso3166code = models.CharField(db_column='ISO3166code', blank=True, null=True)  # Field name made lowercase.
    diocese = models.CharField(db_column='Diocese', blank=True, null=True)  # Field name made lowercase.
    lat = models.CharField(db_column='Lat', blank=True, null=True)  # Field name made lowercase.
    long = models.CharField(db_column='Long', blank=True, null=True)  # Field name made lowercase.
    bells = models.CharField(db_column='Bells', blank=True, null=True)  # Field name made lowercase.
    ur = models.CharField(db_column='UR', blank=True, null=True)  # Field name made lowercase.
    semitones = models.CharField(db_column='Semitones', blank=True, null=True)  # Field name made lowercase.
    wt = models.CharField(db_column='Wt', blank=True, null=True)  # Field name made lowercase.
    app = models.CharField(db_column='App', blank=True, null=True)  # Field name made lowercase.
    note = models.CharField(db_column='Note', blank=True, null=True)  # Field name made lowercase.
    hz = models.CharField(db_column='Hz', blank=True, null=True)  # Field name made lowercase.
    details = models.CharField(db_column='Details', blank=True, null=True)  # Field name made lowercase.
    gf = models.CharField(db_column='GF', blank=True, null=True)  # Field name made lowercase.
    toilet = models.CharField(db_column='Toilet', blank=True, null=True)  # Field name made lowercase.
    simulator = models.CharField(db_column='Simulator', blank=True, null=True)  # Field name made lowercase.
    extrainfo = models.CharField(db_column='ExtraInfo', blank=True, null=True)  # Field name made lowercase.
    webpage = models.CharField(db_column='WebPage', blank=True, null=True)  # Field name made lowercase.
    affiliations = models.CharField(db_column='Affiliations', blank=True, null=True)  # Field name made lowercase.
    ng = models.CharField(db_column='NG', blank=True, null=True)  # Field name made lowercase.
    postcode = models.CharField(db_column='Postcode', blank=True, null=True)  # Field name made lowercase.
    practice = models.CharField(db_column='Practice', blank=True, null=True)  # Field name made lowercase.
    ovhaulyr = models.CharField(db_column='OvhaulYr', blank=True, null=True)  # Field name made lowercase.
    contractor = models.CharField(db_column='Contractor', blank=True, null=True)  # Field name made lowercase.
    tuneyr = models.CharField(db_column='TuneYr', blank=True, null=True)  # Field name made lowercase.
    lgrade = models.CharField(db_column='LGrade', blank=True, null=True)  # Field name made lowercase.
    bldgid = models.CharField(db_column='BldgID', blank=True, null=True)  # Field name made lowercase.
    churchcare = models.CharField(db_column='ChurchCare', blank=True, null=True)  # Field name made lowercase.
    chrassetid = models.CharField(db_column='CHRAssetID', blank=True, null=True)  # Field name made lowercase.
    towerbase = models.CharField(db_column='TowerBase', blank=True, null=True)  # Field name made lowercase.
    doveid = models.CharField(db_column='DoveID', blank=True, null=True)  # Field name made lowercase.
    snlat = models.CharField(db_column='SNLat', blank=True, null=True)  # Field name made lowercase.
    snlong = models.CharField(db_column='SNLong', blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return f'{self.place}  ({self.dedicn})'


    class Meta:
        managed = False
        db_table = 'dove_towers'
        ordering = ["place", "dedicn"]