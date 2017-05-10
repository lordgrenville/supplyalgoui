import re
import argparse
from flask import *
from tools.forms import PrimaryForm
from tools.functionality import Functionality, userInfo, yotamTime

# parsing the init arguments for access to the redisDB
def parsing():
    parser = argparse.ArgumentParser(description='run the app')
    parser.add_argument('-cr', '--crdb', dest="crdb", type=str)
    parser.add_argument('-dr', '--drdb', dest="drdb", type=str)
    parser.add_argument('-redind', '--redisindex', dest="redisindex", type=str)
    parser.add_argument('-redmast', '--redismastername', dest="redismastername", type=str)
    parser.add_argument('-redip', '--redisipvec', dest="redisipvec", type=str)
    parser.add_argument('-esip', '--esippush', dest="esippush", type=str)
    parser.add_argument('-esind', '--esindnpush', dest="esindnpush", type=str)
    parser.add_argument('-tz', '--timezone', dest="timezone", type=str)
    parser.add_argument('-lvl', '--log_level', dest="log_level", type=str)
    args = parser.parse_args()
    return args

# this method initialises the flask app
def get_app(myfunc, new_update, config_filename):
    app = Flask(__name__)
    # app.config.from_object(config_filename)
    app.config['SECRET_KEY'] = 'os.urandom(10)'

    # home view
    @app.route('/', methods=['GET', 'POST'])
    def home():
        form = PrimaryForm(request.form)

        if request.method == 'GET':
            return render_template('base_home.html', form=form, step=0)

        if form.campaignID.data == '':
            flash('You didn\'t enter a campaign ID!')
            return render_template("base_home.html", form=form, step=0)

        options = {'bid':form.curbid.data, 'maxbid':form.maxbid.data, 'lowerbid':form.minbid.data,
                   'frequency_cap':form.frequency_cap.data, 'status':form.status.data}

        new_update.get_info(form.campaignID.data.strip(), form.dsp.data)
        # adds CID and DSP to new_updates. the .strip() removes trailing spaces

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

        #store information as a dict
        if all(v == '' for v in options.values()):
            info = {'Name': old_redis['name'][new_update.campaign_id],
                    'Status':old_redis['status'][new_update.campaign_id],
                    'Bid':old_redis['bid'][new_update.campaign_id],
                    'Maximum Bid':old_redis['maxbid'][new_update.campaign_id],
                    'Minimum Bid':old_redis['lowerbid'][new_update.campaign_id],
                    'Cap': int(old_redis['frequency_cap'][new_update.campaign_id])}

            if info['Status'] == True:
                info['Status'] = "Active"
            else:
                info['Status'] = "Paused"

            return render_template("base_home.html", info=info, DSP=new_update.DSP, id=new_update.name, form=form,
                                   step=1, rows=0)

        for x in options.keys():
            if options[x] != '':
                new_update.updates[x] = options[x]

        new_time = yotamTime()

        if 'status' in new_update.updates:
            #store the old value
            if old_redis['status'][new_update.campaign_id] == True:
                new_update.oldvalues['status'] = "Activated"
            else:
                new_update.oldvalues['status'] = "Paused"

            #update the redis over here
            if new_update.updates['status'] == 'Activated':
                old_redis['status'][new_update.campaign_id] = True
            else:
                old_redis['status'][new_update.campaign_id] = False

        if 'frequency_cap' in new_update.updates:
            try:
                my_cap = float(new_update.updates['frequency_cap'])
                #validate whole number, set max and min
                if my_cap.is_integer() and my_cap > 0 and my_cap <= 500:
                    #store the old value
                    new_update.oldvalues['frequency_cap'] = old_redis['frequency_cap'][new_update.campaign_id]
                    #update the new value
                    old_redis['frequency_cap'][new_update.campaign_id] = my_cap

                else:
                    flash("Sorry, the frequency cap must be a whole number between 0 and 300")
                    return render_template("base_home.html", form=form, step=0)

            except ValueError:
                    flash("Sorry, the cap you enter must be in integer form, e,g, 3")
                    return render_template("base_home.html", form=form, step=0)
            except:
                flash("Unknown error")
                return render_template("base_home.html", form=form, step=0)
        if 'bid' in new_update.updates:
            try:
                my_bid = float(new_update.updates['bid'])
                if my_bid > 0 and my_bid <= 20:     #validating not blank, setting min/max
                    old_bid = old_redis['bid'][new_update.campaign_id]
                    new_update.oldvalues['bid'] = old_bid
                    old_redis['bid'][new_update.campaign_id] = my_bid
                else:
                    flash("Sorry, your bid must be between 0 and 20.")
                    return render_template("base_home.html", form=form, step=0)

            except ValueError:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)

        if 'lowerbid' in new_update.updates:
            try:
                my_lowerbid = float(new_update.updates['lowerbid'])
                if my_lowerbid > 0 and my_lowerbid <= 20:  # validating not blank, setting min/max
                    old_bid = old_redis['lowerbid'][new_update.campaign_id]
                    new_update.oldvalues['lowerbid'] = old_bid
                    old_redis['lowerbid'][new_update.campaign_id] = my_lowerbid
                else:
                    flash("Sorry, your bid must be between 0 and 20.")
                    return render_template("base_home.html", form=form, step=0)

            except ValueError:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)

        if 'maxbid' in new_update.updates:
            try:
                my_maxbid = float(new_update.updates['maxbid'])
                if my_maxbid > 0 and my_maxbid <= 20:  # validating not blank, setting min/max
                    old_bid = old_redis['maxbid'][new_update.campaign_id]
                    new_update.oldvalues['maxbid'] = old_bid
                    old_redis['maxbid'][new_update.campaign_id] = my_maxbid
                else:
                    flash("Sorry, your bid must be between 0 and 20.")
                    return render_template("base_home.html", form=form, step=0)

            except ValueError:
                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                return render_template("base_home.html", form=form, step=0)
        # update time
        old_redis['useruts'][new_update.campaign_id] = new_time

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
            return render_template("algo_response.html", term=m)

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