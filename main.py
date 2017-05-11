import re
from flask import *
from tools.forms import PrimaryForm
from tools.functionality import Functionality, userInfo, yotamTime, parsing, numberChecker

# initialise a flask object, and call the run method. this will start our site!
def get_app(myfunc, new_update, config_filename):
    app = Flask(__name__)

    # setting a secret key in the config dict - this is needed so that we can flash messages
    app.secret_key = 'os.urandom(24)'

    #home view
    @app.route('/')
    def home():
        form = PrimaryForm(request.form)
        return render_template('base_home.html', form=form, step=0)

    #response view - same URL, though
    @app.route('/', methods=['POST'])
    def response():

        form = PrimaryForm(request.form)

        #check campaign ID exists
        if form.campaignID.data == '':
            flash('You didn\'t enter a campaign ID!')
            return render_template("base_home.html", form=form, step=0)

        #create a dict to store form information
        options = {'bid':form.curbid.data, 'maxbid':form.maxbid.data, 'lowerbid':form.minbid.data,
                   'frequency_cap':form.frequency_cap.data, 'status':form.status.data}

        #store campaign ID and DSP in a new_update, strip trailing spaces
        new_update.get_info(form.campaignID.data.strip(), form.dsp.data)

        # we need to search old_redis for the correct dict, and then the correct campaign_id, and then alter it
        #Es.log
        try:
            old_redis = myfunc.getdoc(new_update.DSP)
        except SystemExit as m:
            return render_template("algo_response.html", term=m)

        if new_update.campaign_id not in old_redis['status']:
            flash("It looks like the campaign you're trying to update isn't in the algorithm. Please check all"
                  " of your parameters and try again.")
            return render_template("base_home.html", form=form, step=0)

        # Es.log try - except
        new_update.get_name(old_redis['name'][new_update.campaign_id])

        #if there are no updates in the form, get all of the old data and store it in a dict
        if all(v == '' for v in options.values()):
            info = {'Name': old_redis['name'][new_update.campaign_id],
                    'Status':old_redis['status'][new_update.campaign_id],
                    'Bid':old_redis['bid'][new_update.campaign_id],
                    'Maximum Bid':old_redis['maxbid'][new_update.campaign_id],
                    'Minimum Bid':old_redis['lowerbid'][new_update.campaign_id],
                    'Cap': int(old_redis['frequency_cap'][new_update.campaign_id])}

            #change the term for status from true/false to active/paused
            if info['Status'] == True:
                info['Status'] = "Active"
            else:
                info['Status'] = "Paused"

            return render_template("base_home.html", info=info, DSP=new_update.DSP, id=new_update.name, form=form,
                                   step=1, rows=0)

        #otherwise, if there ARE updates in the form, add what is there to new_updates
        for x in options.keys():
            if options[x] != '':
                new_update.updates[x] = options[x]

        #update the userts (timestamp)
        new_time = yotamTime()

        #search for each parameter and update it
        if 'status' in new_update.updates:
            #store the old value
            if old_redis['status'][new_update.campaign_id] == True:
                new_update.oldvalues['status'] = "Activated"
            else:
                new_update.oldvalues['status'] = "Paused"

            #update the redis dict
            if new_update.updates['status'] == 'Activated':
                old_redis['status'][new_update.campaign_id] = True
            else:
                old_redis['status'][new_update.campaign_id] = False

        #...and so on
        if 'frequency_cap' in new_update.updates:
            if numberChecker(new_update.updates['frequency_cap'],0,500) == "good":
                new_update.oldvalues['frequency_cap'] = old_redis['frequency_cap'][new_update.campaign_id]
                old_redis['frequency_cap'][new_update.campaign_id] = new_update.updates['frequency_cap']
            elif numberChecker(new_update.updates['frequency_cap'],0,500) == "bad size":
                flash("Sorry, the frequency cap must be a whole number between 0 and 300")
                return render_template("base_home.html", form=form, step=0)
            else:
                flash("Unknown error. check your frequency cap is a number, e.g. 3")
                return render_template("base_home.html", form=form, step=0)

        if 'bid' in new_update.updates:
            if numberChecker(new_update.updates['bid'],0,20) == "good":
                old_bid = old_redis['bid'][new_update.campaign_id]
                new_update.oldvalues['bid'] = old_bid
                old_redis['bid'][new_update.campaign_id] = new_update.updates['bid']
            elif numberChecker(new_update.updates['bid'],0,20) == "bad size":
                flash("Sorry, your bid must be between 0 and 20.")
                return render_template("base_home.html", form=form, step=0)
            else:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)

        if 'lowerbid' in new_update.updates:
            if numberChecker(new_update.updates['lowerbid'],0,20) == "good":
                old_bid = old_redis['lowerbid'][new_update.campaign_id]
                new_update.oldvalues['lowerbid'] = old_bid
                old_redis['lowerbid'][new_update.campaign_id] = new_update.updates['lowerbid']
            elif numberChecker(new_update.updates['lowerbid'],0,20) == "bad size":
                flash("Sorry, your bid must be between 0 and 20.")
                return render_template("base_home.html", form=form, step=0)
            else:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)

        if 'maxbid' in new_update.updates:
            if numberChecker(new_update.updates['maxbid'],0,20) == "good":
                old_bid = old_redis['maxbid'][new_update.campaign_id]
                new_update.oldvalues['maxbid'] = old_bid
                old_redis['maxbid'][new_update.campaign_id] = new_update.updates['maxbid']
            elif numberChecker(new_update.updates['maxbid'],0,20) == "bad size":
                flash("Sorry, your bid must be between 0 and 20.")
                return render_template("base_home.html", form=form, step=0)
            else:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)

        # update time
        old_redis['useruts'][new_update.campaign_id] = new_time

        #save info for old and new values in dicts to display to the user
        changes = []
        olds = []
        news = []
        for k, v in new_update.updates.items():
            if v != '':
                changes.append(k.title())
                olds.append(new_update.oldvalues[k])
                news.append(new_update.updates[k])
        rows = len(changes)

        #return landing page to user with success/failure message
        try:
            myfunc.mr.set_doc_by_dsp(new_update.DSP,old_redis)
            return render_template("base_home.html", id=new_update.name, DSP=new_update.DSP.title(), changes=changes,
                                   rows=rows, olds=olds, news=news, step=2, form=form)
        except SystemExit as m:
            #ES as log
            return render_template("algo_response.html")

        #if nothing else, return 404 error
        abort(404)

    app.debug = False
    return app

if __name__ == '__main__':

    #instantiate parser
    args = parsing()

    crdb = args.crdb
    drdb = args.drdb
    redisindex = args.redisindex
    redismastername = args.redismastername
    redisipvec = args.redisipvec
    _redisipvec = re.split(",", redisipvec)
    redisipvec = []
    for ip in _redisipvec:
        ip = re.split(":", ip)
        redisipvec.append((ip[0], ip[1]))
    esippush = args.esippush
    esindnpush = args.esindnpush
    timezone = args.timezone
    log_level = args.log_level

    # instantiate two objects to store data
    myfunc = Functionality(crdb, drdb, redisindex, redismastername,
                           redisipvec, esippush, esindnpush, timezone, log_level)
    new_update = userInfo()

    # instantiate flask app
    app = get_app(myfunc, new_update, "settings")
    app.run()