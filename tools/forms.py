from wtforms import Form, SelectField, StringField, IntegerField, DecimalField, validators
class PrimaryForm(Form):
    campaignID = StringField('Campaign ID',[validators.Length(min=1, max=99, message="Please enter a campaign ID")])
    choice = SelectField('Choice', choices=[('lowerbid', 'Minimum Bid'), ('maxbid', 'Maximum Bid'), ('bid', 'Current Bid'),('frequency_cap', 'Frequency Cap'), ('status', 'Status')])
    dsp = SelectField('DSP',choices=[('nuviad', 'Nuviad'),('pocket', 'Pocket')])  #upper case for display, but must be lower case for redisDB!

class BidForm(Form):
    bid = StringField('Bid', [validators.Length(min=1,message="Please enter a bid")])

class CapForm(Form):
    frequency_cap = IntegerField('Cap', [validators.Length(min=1, message="Please enter a cap")])

class StatusForm(Form):
    status = SelectField('Status', choices=[('Activated', 'Activated'),('Paused', 'Paused')])