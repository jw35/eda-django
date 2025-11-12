from django.contrib import admin
from django.forms import ModelForm
from django.utils.html import urlize, escape
from django.utils.safestring import mark_safe

from search_admin_autocomplete.admin import SearchAutoCompleteAdmin

from simple_history.admin import SimpleHistoryAdmin

# Register your models here.

from .models import Contact, Tower, ContactMap, Photo, Website, DoveTower

from position_widget.widgets import PositionInput

admin.site.site_header = "Ely DA Admin"
admin.site.site_title = "Database admin"
admin.site.index_title = "Database admin"


class ContactInline(admin.TabularInline):
    model = Tower.other_contacts.through
    verbose_name = "other contact"
    extra = 0
    #classes = ["collapse"]

class PrimaryContactInline(admin.TabularInline):
    model = Tower
    fields = ["__str__"]
    readonly_fields = ["__str__"]
    verbose_name = "primary contact"
    extra = 0
    can_delete = False

class TowerInline(admin.TabularInline):
    model = Tower.other_contacts.through
    fields = ["role", "tower", "publish"]
    readonly_fields = ["role", "tower", "publish"]
    verbose_name = "as other contact"
    extra = 0
    can_delete = False

class WebsiteInline(admin.TabularInline):
    model = Website
    extra = 0
    #classes = ["collapse"]

class PhotoInline(admin.StackedInline):
    model = Photo
    fields = ["tower", "photo", "photo_tag", "photo_height", "photo_width"]
    readonly_fields = ["tower", "photo_tag", "photo_height", "photo_width"]
    extra = 0
    #classes = ["collapse"]

class PhotoAdmin(SimpleHistoryAdmin):
    fields = ["tower", "photo", "photo_tag", "photo_height", "photo_width"]
    readonly_fields = ["tower", "photo_tag", "photo_height", "photo_width"]


class ContactAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    inlines= [PrimaryContactInline, TowerInline]
    search_fields = ["name", "phone", "phone2", "email"]
    search_help_text = "Search by name, phone number or email"

class MyTowerAdminForm(ModelForm):
    class Meta:
        model = Tower
        widgets = {
            'position': PositionInput(height=300, lat1=52.75959, lng1=-0.46869, lat2=52.07286, lng2=0.58795)
        }
        fields = '__all__' # required for Django 3.x

class TowerAdmin(SearchAutoCompleteAdmin, SimpleHistoryAdmin):
    form = MyTowerAdminForm
    inlines = [WebsiteInline, ContactInline, PhotoInline]
    list_display = ["__str__", "district", "bells"]
    list_filter = ["district", "report", "bells", "ringing_status", "ring_type", "practice_day"]
    search_fields = ["place", "dedication", "full_dedication", "nickname"]
    search_help_text = "Search by place or dedication"
    readonly_fields = ["dove_link_html", "bellboard_link_html", "felstead_link_html"]

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
            "Contacts, links and notes", {
                "fields": (
                    "primary_contact",
                    "contact_restriction",
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

class DoveTowerAdmin(SearchAutoCompleteAdmin):
    search_fields = ["place", "dedicn", "towerid", "ringid"]
    search_help_text = "Search by place or dedication (or tower or ring  ID)"
    list_display = ["__str__", "bells"]
    list_filter = ["bells", "ringtype", ("ur", admin.EmptyFieldListFilter), "county", "country", "diocese"]

    def get_readonly_fields(self, request, obj=None):
        return [f.name for f in obj._meta.fields]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(Contact, ContactAdmin)
admin.site.register(Tower, TowerAdmin)
admin.site.register(DoveTower, DoveTowerAdmin)
admin.site.register(Photo, PhotoAdmin)
