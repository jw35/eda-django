from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError

from tower_database.models import Tower


class Command(BaseCommand):
    help = 'Set/reset permission groups for the Tower Database'

    '''
    def add_arguments(self, parser):
        parser.add_argument("--file", help="Import from CSV, rather than collecting directly")
    '''

    def handle(self, *args, **options):

        # Create custom permission labels
        permissions = [
            ('admin_cambridge', 'Can admin Cambridge towers'),
            ('admin_ely', 'Can admin Ely towers'),
            ('admin_huntingdon', 'Can admin Huntingdon towers'),
            ('admin_wisbech', 'Can admin Wisbech towers')
        ]

        content_type = ContentType.objects.get_for_model(Tower)
        for permission in permissions:
            Permission.objects.get_or_create(
                codename=permission[0],
                name=permission[1],
                content_type=content_type,
            )

        # Sets of permissions to allocate
        ro_permissions = ('view_contact' , 'view_contactperson', 'view_dove', 'view_photo', 'view_tower','view_website')

        admin_permissions = ('add_contact', 'change_contact', 'view_contact',
                 'add_contactperson', 'change_contactperson', 'delete_contactperson', 'view_contactperson',
                 'view_dove',
                 'add_photo', 'change_photo', 'delete_photo', 'view_photo',
                 'add_tower', 'change_tower', 'delete_tower', 'view_tower',
                 'add_website', 'change_website', 'delete_website', 'view_website'
                 )

        district_admin_permissions = ('add_contactperson', 'change_contactperson', 'view_contactperson')

        # Get all existing permissions
        all_permissions = Permission.objects.filter(content_type__app_label='tower_database')

        # A read-only group just containing the view permissions
        read_only, created = Group.objects.get_or_create(name='Tower Database read-only')
        read_only.permissions.clear()
        for perm in all_permissions:
            if perm.codename in ro_permissions:
                read_only.permissions.add(perm)

        # An admin group containing all of add/change/delete/view(except for Dove)
        admin, created  = Group.objects.get_or_create(name='Tower Database admin')
        admin.permissions.clear()
        for perm in all_permissions:
            if perm.codename in admin_permissions:
                admin.permissions.add(perm)

        # A set of groups giving some update access to Towers and related models in each of the districts
        for district in Tower.Districts.labels:
            group, created  = Group.objects.get_or_create(name=f'Tower Database admin {district}')
            group.permissions.clear()
            for perm in all_permissions:
                if (perm.codename == f'admin_{district.lower()}'
                    or perm.codename in ro_permissions
                    or perm.codename in district_admin_permissions):
                     group.permissions.add(perm)


'''


**contact add_contact
**contact change_contact
**contact delete_contact
contact view_contact
**contactmap add_contactmap
**contactmap change_contactmap
**contactmap delete_contactmap
contactmap view_contactmap
**dove add_dove
**dove change_dove
**dove delete_dove
dove view_dove
historicalcontact add_historicalcontact
historicalcontact change_historicalcontact
historicalcontact delete_historicalcontact
historicalcontact view_historicalcontact
historicalcontactmap add_historicalcontactmap
historicalcontactmap change_historicalcontactmap
historicalcontactmap delete_historicalcontactmap
historicalcontactmap view_historicalcontactmap
historicaltower add_historicaltower
historicaltower change_historicaltower
historicaltower delete_historicaltower
historicaltower view_historicaltower
historicalwebsite add_historicalwebsite
historicalwebsite change_historicalwebsite
historicalwebsite delete_historicalwebsite
historicalwebsite view_historicalwebsite
**photo add_photo
**photo change_photo
**photo delete_photo
photo view_photo
**tower add_tower
**tower change_tower
**tower delete_tower
tower view_tower
**website add_website
**website change_website
**website delete_website
website view_website

'''