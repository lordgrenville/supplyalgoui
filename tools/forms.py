from wtforms import Form, SelectField, StringField, IntegerField, DecimalField, validators

class RegistrationForm(Form):
    campaignID = StringField('Campaign ID',[validators.Length(min=1, max=99, message="Please enter a campaign ID")])
    choice = SelectField('Choice', choices=[('lowerbid', 'Minimum Bid'), ('max_bid', 'Maximum Bid'), ('cur_bid', 'Current Bid'),('cap', 'Cap'), ('status', 'Status')])
    dsp = SelectField('DSP',choices=[('Nuviad', 'Nuviad'),('Pocket', 'Pocket')])

class BidForm(Form):
    bid = DecimalField('Bid', places=2)

class CapForm(Form):
    frequency_cap = IntegerField('Cap',[validators.input_required('Please please please me'), validators.number_range(0,999,'Your bid must be between 0 and 999')])

class StatusForm(Form):
    status = SelectField('Status', choices=[('Activated', 'Activated'),('Paused', 'Paused')])