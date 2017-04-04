from wtforms import Form, SelectField, StringField, IntegerField, DecimalField, validators
class PrimaryForm(Form):
    campaignID = StringField('Campaign ID',[validators.Length(min=1, max=99, message="Please enter a campaign ID")])
    choice = SelectField('Choice', choices=[('lowerbid', 'Minimum Bid'), ('maxbid', 'Maximum Bid'), ('bid', 'Current Bid'),('frequency_cap', 'Cap'), ('status', 'Status')])
    dsp = SelectField('DSP',choices=[('Nuviad', 'Nuviad'),('Pocket', 'Pocket')])

class BidForm(Form):
    bid = DecimalField('Bid', places=2)

class CapForm(Form):
    frequency_cap = IntegerField('Cap',[validators.MyValidator()])

class StatusForm(Form):
    status = SelectField('Status', choices=[('Activated', 'Activated'),('Paused', 'Paused')])