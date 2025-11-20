from django.contrib import admin
from django.contrib.auth import get_permission_codename
from django.forms import ModelForm
from django.utils.html import urlize, escape
from django.utils.safestring import mark_safe

from search_admin_autocomplete.admin import SearchAutoCompleteAdmin

from simple_history.admin import SimpleHistoryAdmin

# Register your models here.

from .models import ContactPerson, Contact, Tower, Photo, Website, Dove

from position_widget.widgets import PositionInput

admin.site.site_header = "Ely DA Admin"
admin.site.site_title = "Database admin"
admin.site.index_title = "Database admin"

class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 0

class ContactInlineForPerson(admin.TabularInline):
    model = Contact
    fields = ["role", "tower", "publish", "primary"]
    readonly_fields = ["role", "tower", "publish", "primary"]
    extra = 0

class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0

class WebsiteInline(admin.TabularInline):
    model = Website
    extra = 0
    #classes = ["collapse"]

class PhotoInline(admin.StackedInline):
    model = Photo
    fields = ["tower", "photo", "photo_tag", "photo_height", "photo_width"]
    readonly_fields = ["photo_height", "photo_width", "photo_tag"]
    extra = 0
    #classes = ["collapse"]

class PhotoAdmin(SimpleHistoryAdmin):
    fields = ["tower", "photo", "photo_tag", "photo_height", "photo_width"]
    readonly_fields = ["photo_height", "photo_width", "photo_tag"]
    list_display = ["tower", "photo_height", "photo_width", "photo_tag"]

    def has_change_permission(self, request, obj=None):
        if obj == None:
            return True
        elif request.user.has_perm(f"{self.opts.app_label}.admin_{obj.tower.get_district_display().lower()}"):
            return True
        else:
            return super().has_change_permission(request, obj)

class WebsiteAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    search_fields = ["website", "target"]
    search_help_text = "Search by website address or link text"
    fields = ["tower", "link_text", "website"]
    list_display = ["tower", "link_text", "website"]

    def has_change_permission(self, request, obj=None):
        if obj == None:
            return True
        elif request.user.has_perm(f"{self.opts.app_label}.admin_{obj.tower.get_district_display().lower()}"):
            return True
        else:
            return super().has_change_permission(request, obj)

class ContactPersonAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    search_fields = ["forename", "name", "personal_phone", "personal_phone2", "personal_email"]
    search_help_text = "Search by name, phone number or email"
    list_display = ["name", "title", "forename", "personal_phone", "personal_phone2", "personal_email"]
    inlines = [ContactInlineForPerson]

class ContactAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    list_display = ["tower", "role", "person", "email", "form"]
    readonly_fields = ["tower"]

    def has_change_permission(self, request, obj=None):
        if obj == None:
            return True
        elif request.user.has_perm(f"{self.opts.app_label}.admin_{obj.tower.get_district_display().lower()}"):
            return True
        else:
            return super().has_change_permission(request, obj)

class MyTowerAdminForm(ModelForm):
    class Meta:
        model = Tower
        widgets = {
            'position': PositionInput(height=300, lat1=52.75959, lng1=-0.46869, lat2=52.07286, lng2=0.58795)
        }
        fields = '__all__' # required for Django 3.x

class TowerAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    form = MyTowerAdminForm
    inlines = [ContactInline, WebsiteInline, PhotoInline]
    list_display = ["__str__", "district", "bells"]
    list_filter = ["district", "report", "bells", "ringing_status", "ring_type", "practice_day"]
    search_fields = ["place", "dedication", "full_dedication", "nickname"]
    search_help_text = "Search by place or dedication"
    readonly_fields = ["dove_link_html", "bellboard_link_html", "felstead_link_html"]

    def has_change_permission(self, request, obj=None):
        '''
        Towers can be edited by anyone with the 'admin_[district]" permission for the,
        district of this object, or who would be able to change it under the Djago standard rules
        '''
        if obj == None:
            return True
        elif request.user.has_perm(f"{self.opts.app_label}.admin_{obj.get_district_display().lower()}"):
            return True
        else:
            return super().has_change_permission(request, obj)


    def dove_link_html(self, instance):
        return mark_safe(urlize(instance.dove_link, nofollow=True, autoescape=True))

    def bellboard_link_html(self, instance):
        return mark_safe(urlize(instance.bellboard_link, nofollow=True, autoescape=True))

    def felstead_link_html(self, instance):
        return mark_safe(urlize(instance.felstead_link, nofollow=True, autoescape=True))

    fieldsets = [
        (
            None, {
                "fields": (
                    "place",
                    "county",
                    "dedication",
                    "include_dedication",
                    "full_dedication",
                    "nickname",
                    "district",
                    "report",
                    "peals",
                )
            }
        ),
        (
            "Ringing", {
                "fields": (
                    "ringing_status",
                    "service",
                    "practice",
                    "practice_day",
                    "practice_weeks",
                    "travel_check",
                )
            }
        ),
        (
            "Bells", {
                "fields": (
                    "bells",
                    "ring_type",
                    "weight",
                    "note",
                    "gf",
                )
            }
        ),
        (
            "Location", {
                "fields": (
                    "os_grid",
                    "postcode",
                    "lat",
                    "lng",
                    "position",
                )
            }
        ),
        (
            "Links and notes", {
                "fields": (
                    "dove_ringid",
                    "dove_towerid",
                    "dove_link_html",
                    "bellboard_link_html",
                    "towerbase_id",
                    "felstead_link_html",
                    "notes",
                    "long_notes",
                    "maintainer_notes",
                )
            }
        )
    ]

class DoveAdmin(SearchAutoCompleteAdmin):
    search_fields = ["place", "dedicn", "towerid", "ringid"]
    search_help_text = "Search by place or dedication (or tower or ring  ID)"
    list_display = ["__str__", "county", "country", "bells"]
    list_filter = ["bells", "ringtype", ("ur", admin.EmptyFieldListFilter), "county", "country", "diocese"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in obj._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(ContactPerson, ContactPersonAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Tower, TowerAdmin)
admin.site.register(Dove, DoveAdmin)
admin.site.register(Photo, PhotoAdmin)
admin.site.register(Website, WebsiteAdmin)
