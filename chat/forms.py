from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

class MessageForm(forms.Form):
    content = forms.CharField(
        widget=CKEditor5Widget(
            attrs={"class": "django_ckeditor_5"},
            config_name='extends'
        ),
        label='',
        required=False
    )