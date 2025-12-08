from django import forms


class CSVImportForm(forms.Form):
    """Form for uploading CSV file to import packages"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: category, type, item, labor_Phase_Name, Unit Price'
    )
    property_type = forms.CharField(
        max_length=200,
        initial='Residential',
        help_text='Property type for all imported packages (e.g., Residential, Commercial, Industrial)'
    )
    overwrite_existing = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Overwrite existing packages with the same name'
    )
