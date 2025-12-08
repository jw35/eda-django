from django.contrib import admin
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

from multiselectfield import MultiSelectField
from simple_history.models import HistoricalRecords
from OSGridConverter import latlong2grid

import os.path
import re
import uuid

from collections import defaultdict


# Shortcut for invalidating the cache (used for GEioJANGO) when 
# a model instance is saved or deleted

class CacheInvalidayingModel(models.Model):

    class Meta:
        abstract = True

    def save(self, **kwargs):
        super().save(**kwargs)
        cache.clear()

    def delete(self, **kwargs):
        super().save(**kwargs)
        cache.clear()

# Create your models here.

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
    WEEK_PHRASE_PATTERN = re.compile(r'\bNot\b(?! Bank Holiday)|1st|2nd|3rd|4th|5th|\bAlternate\b', re.IGNORECASE)


class Tower(CacheInvalidayingModel):

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
        MONDAY = '1'
        TUESDAY = '2'
        WEDNESDAY = '3'
        THURSDAY = '4'
        FRIDAY = '5'
        SATURDAY = '6'
        SUNDAY = '7'

    class PracticeWeeks(models.TextChoices):
        NOT = 'not', 'Not'
        W1 = '1st', '1st'
        W2 = '2nd', '2nd'
        W3 = '3rd', '3rd'
        W4 = '4th', '4th'
        W5 = '5th', '5th'
        ALT = 'alternate', 'Alternate'

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
    service = models.CharField(max_length=200, blank=True, validators=[time_validator], help_text="Short description of normal service ringing. No initial capital (unless day of week)")
    practice = models.CharField(max_length=200, blank=True, validators=[time_validator], help_text="Short description of normal practice ringing. No initial capital (unless day of week)")
    practice_day = models.CharField(max_length=9, blank=True, choices=Days, help_text="Day of the week of main practice")
    practice_weeks = MultiSelectField(max_length=50, blank=True, choices=PracticeWeeks, validators=[week_validator], help_text="Week(s) of the month for main practice if not all")
    travel_check = models.BooleanField(default=False, help_text="Check before travelling to practices?")
    bells = models.PositiveIntegerField(null=True, blank=True, help_text="Number of ringable bells",validators=[bell_validator])
    ring_type = models.CharField(max_length=20, blank=True, choices=RingTypes)
    weight =models.CharField(max_length=50, blank=True, validators=[weight_validator], help_text="Use ‘15-3-13’ or ‘6cwt’")
    note = models.CharField(max_length=10, blank=True, validators=[note_validator], help_text="Use A-G optionally followed by '#' or ‘b’")
    gf = models.BooleanField(blank=True, null=True, verbose_name="Ground Floor?")
    postcode = models.CharField(max_length=10, blank=True, validators=[postcode_validator])
    latlng = models.CharField(max_length=20, blank=True, verbose_name='Location')
    peals = models.PositiveIntegerField(null=True , blank=True, help_text="Peals in most recent Annual Report")
    dove_towerid = models.CharField(max_length=10, blank=True, verbose_name="Dove TowerID")
    dove_ringid = models.CharField(max_length=10, blank=True, verbose_name="Dove RingID")
    towerbase_id = models.CharField(max_length=10, blank=True, verbose_name="Towerbase ID")
    notes = models.CharField(max_length=100, blank=True, help_text="For display, especially in the Annual Report")
    long_notes = models.TextField(blank=True, help_text="For display when space isn’t at a premium")
    maintainer_notes = models.TextField(blank=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["place", "dedication"]
        constraints = [
            models.UniqueConstraint(fields=["place", "dedication"], name="unique_place_dedication",
                violation_error_message="Can't have two towers with the same place and dedication")
        ]

    def __str__(self):
        return f'{self.place} - {self.dedication}'

    def get_absolute_url(self):
        return reverse("tower_detail", kwargs={"pk": self.pk})

    @property
    def practice_weeks_text(self):
        n = ''
        if 'not' in self.practice_weeks:
            n = 'not '
        return n + ', '.join([w for w in self.practice_weeks if w != 'not'])

    @property
    def primary_contact(self):
        for contact in self.contact_set.all():
            if contact.primary:
                return contact
        return None

    @property
    def other_contacts(self):
        return [c for c in self.contact_set.all() if not c.primary]

    @property
    def dove_link(self):
        return f"https://dove.cccbr.org.uk/tower/{self.dove_towerid}"

    @property
    def bellboard_link(self):
        return f"https://bb.ringingworld.co.uk/search?dove_tower={self.dove_towerid}"

    @property
    def felstead_link(self):
        return f"https://felstead.cccbr.org.uk/tbid.php?tid={self.towerbase_id}"

    @property
    def lat(self):
        return float(self.latlng.split(',')[0])

    @property
    def lng(self):
        return float(self.latlng.split(',')[1])

    @property
    def os_grid(self):
        g = str(latlong2grid(self.lat, self.lng))
        return g[0:2] + g[3:6] + g[9:12]
    os_grid.fget.short_description = "OS Grid"

    def clean(self):

        """
        Make various cross-field checks. Many of these are a bit heuristic.
        """

        errors = defaultdict(list)

        # ringing & saervice/practice
        if self.ringing_status == Tower.RingingStatus.NONE and (self.service or self.practice):
            errors['ringing_status'].append(f"Inconsistent with Service or Practice")

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
            # Is every relevant phrase in `practice` reflected in `practice_weeks`?
            for phrase in TowerConstants.WEEK_PHRASE_PATTERN.findall(self.practice):
                if phrase.lower() not in self.practice_weeks:
                    errors['practice_weeks'].append(f"'{phrase}' appears in in Practice")

        # Does everything in `practice_weeks` appear in `practice`
        for phrase in self.practice_weeks:
            if not re.search(r'\b' + phrase + r'\b', self.practice, re.IGNORECASE):
                errors['practice_weeks'].append(f"'{phrase}' doesn't appear in Practice")

        if errors:
            raise ValidationError(errors)


class Contact(CacheInvalidayingModel):

    class Roles(models.TextChoices):
        CONTACT = 'C', 'General'
        BELLS_CONTACT = 'BL', 'Bells'
        BAND_CONTACT = 'BA', 'Band'
        TOWER_CAPTAIN = 'TC'
        RINGING_MASTER = 'RM'
        STEEPLEKEEPER = 'SK'

    class Titles(models.TextChoices):
        MR = 'Mr', 'Mr.'
        MRS = 'Mrs', 'Mrs.'
        MISS = 'Miss', 'Miss.'
        DR = 'Dr', 'Dr.'
        REVD = 'Revd', "The Rev'd"

    role = models.CharField(max_length=30, choices=Roles)
    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    publish = models.BooleanField(default=True, help_text="Publish these details (in the Annual Report, on the web, etc.)")
    primary = models.BooleanField(default=False, help_text="Primary contact for this Tower?")
    title = models.CharField(max_length=5, blank=True, choices=Titles, help_text="Person's title (if required - usually leave blank)")
    forename = models.CharField(max_length=100, blank=True, help_text="Person's forename")
    name = models.CharField(max_length=100, blank=True, help_text="Person's surname, or role title")
    phone1 = models.CharField(max_length=100, blank=True, verbose_name="phone", help_text="Phone number")
    phone2 = models.CharField(max_length=100, blank=True, verbose_name="phone", help_text="Alternate phone number")
    email = models.EmailField(max_length=100, blank=True, help_text="Personal or role email address")
    form = models.URLField(blank=True, help_text="Link to a contact form")
    history = HistoricalRecords()

    class Meta:
        ordering = ["name", "forename", "tower", "email", "phone1", "phone2"]
        constraints = [
            models.UniqueConstraint(fields=["tower"], condition=Q(primary=True),
                name="unique_tower_primary",
                violation_error_message="Towers can only have a single primary contact"),
            models.CheckConstraint(
                condition=~Q(name='') | ~Q(phone1='') | ~Q(phone2='') | ~Q(email='') | ~Q(form=''),
                name="no_non_blank_contact_persons",
                violation_error_message="Need at least one of name, phone, email or form"
            ),
        ]

    def __str__(self):
        return f'{self.tower} ({self.get_role_display()})'

    @property
    @admin.display(ordering="first_name")
    def full_name(self):
        return ' '.join([f for f in (self.title, self.forename, self.name) if f != ''])

    @property
    def as_links(self):
        fragments = []
        if self.full_name:
            fragments.append(escape(self.full_name))
        if self.phone1:
            fragments.append(escape(self.phone1))
        if self.phone2:
            fragments.append(escape(self.phone2))
        if self.email:
            fragments.append(f'<a href="mailto:{escape(self.email)}">{escape(self.email)}</a>')
        if self.form:
            fragments.append(f'<a href="{escape(self.form)}">Contact form</a>')
        return mark_safe(' / '.join(fragments))


class Website(CacheInvalidayingModel):

    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    link_text = models.CharField(max_length=50, blank=True, help_text="Short link text for this website")
    url = models.URLField()
    history = HistoricalRecords()

    class Meta:
        ordering = ["tower", "url"]
        constraints = [
            models.UniqueConstraint(fields=["tower", "url"], name="unique_tower_url",
                violation_error_message="Can't have the same website more than once for the same tower")
        ]

    def __str__(self):
        return f'{self.tower}'


def rename_image(instance, filename):
    suffix = (os.path.splitext(filename)[1]).lower()
    tower = re.sub(' ', '_',f"{instance.tower.place}_{instance.tower.dedication}").lower()
    tower = re.sub(r'[^a-z_]+', '', tower)
    return f"towers/{tower}_{uuid.uuid4()}{suffix}"

class Photo(CacheInvalidayingModel):

    tower = models.ForeignKey(Tower, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=rename_image, height_field="height", width_field="width")
    alt_text = models.CharField(max_length=50, blank=True, help_text="Short text description of the photo")
    height = models.SmallIntegerField(blank=True, null=True, editable=False)
    width = models.SmallIntegerField(blank=True, null=True, editable=False)
    credit = models.CharField(max_length=100, blank=True, help_text = "Source of the photo")
    history = HistoricalRecords()

    class Meta:
        ordering = ["tower", "height"]

    def __str__(self):
        return f'{self.tower} ({self.height}x{self.width})'

    @property
    def img_tag(self):
        return mark_safe(f'<img src="{escape(self.image.url)}" height="{min(self.image.height, 200)} alt="{self.alt_text}">')


# Auto-generated with ./manage.py inspectdb

class Dove(models.Model):
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

    class Meta:
        managed = False
        db_table = 'dove_towers'
        ordering = ["place", "dedicn"]
        verbose_name = 'dove record'

    def __str__(self):
        return f'{self.place}  ({self.dedicn})'

