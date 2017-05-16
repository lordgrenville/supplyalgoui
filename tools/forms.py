from wtforms import Form, SelectField, StringField, validators, SubmitField
class PrimaryForm(Form):
    campaignID = StringField('Campaign ID',[validators.Length(min=1, max=99, message="Please enter a campaign ID")])
    choice = SelectField('Choice', choices=[('lowerbid', 'Minimum Bid'), ('maxbid', 'Maximum Bid'), ('bid', 'Current Bid'),('frequency_cap', 'Frequency Cap'), ('status', 'Status')])
    dsp = SelectField('DSP',choices=[('nuviad', 'Nuviad'),('pocket', 'Pocket')])  #upper case for display, but must be lower case for redisDB!
    curbid = StringField('Current Bid')
    maxbid = StringField('Maximum Bid')
    minbid = StringField('Minimum Bid')
    frequency_cap = StringField('Cap')
    status = SelectField('Status', choices=[('', ''),('Activated', 'Activated'),('Paused', 'Paused')])
    update = SubmitField('Update')
    get_info = SubmitField('Get Information')