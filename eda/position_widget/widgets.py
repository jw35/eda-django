# position_widget.py

from  django.forms.widgets import Input, Script

class PositionInput(Input):
    input_type = 'text'
    template_name = 'position_widget/position.html'

    def __init__(
            self, height=200, width=300, 
            lat1=58.82368, lng1=-10.48650, lat2=50.16105, lng2=2.45950,
            zoom=17,
            attrs=None):
        self.height =height
        self.width = width
        self.lat1 = lat1
        self.lng1 = lng1
        self.lat2 = lat2
        self.lng2 = lng2
        self.zoom = zoom

        super().__init__(attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["widget"]["height"] = self.height
        context["widget"]["width"] = self.width
        context["widget"]["lat1"] = self.lat1
        context["widget"]["lng1"] = self.lng1
        context["widget"]["lat2"] = self.lat2
        context["widget"]["lng2"] = self.lng2
        context["widget"]["zoom"] = self.zoom
        return context

    class Media:
        css = {
            'all': [
                'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
                'position_widget/PositionWidget.css'
                ],
        }
        js = [
                'admin/js/jquery.init.js',
                Script('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js', integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=", crossorigin=""),
                'position_widget/PositionWidget.js'
        ]
