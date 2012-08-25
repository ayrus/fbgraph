from django import forms
from datetime import datetime, timedelta
from pytz import common_timezones

timezones = [(x, x) for x in common_timezones]

def _yearBack():
    '''
    Return a datetime object with a date of 90 days in the past from today.

    '''
    
    return (datetime.now() - timedelta(days=90)).strftime("%d-%m-%Y")

class requestForm(forms.Form):
    
    to_date = forms.CharField(initial = _yearBack())
    
    from_date = forms.CharField(initial = datetime.now().strftime("%d-%m-%Y"))
    
    limit = forms.DecimalField(min_value=100, max_value=500, initial=200)
    
    #Hardcoded value for 'Asia/Kolkata'
    timezone = forms.ChoiceField(choices=timezones, initial = "Asia/Kolkata")
    
