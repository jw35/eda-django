# position_widget.py

from  django.forms.widgets import TextInput, Textarea

class PositionInput(Textarea):
    pass

    class Media:
        css = {
            'all': ['PostitonWidget.css'],
        }
        js = ['PositionWidget.js']
