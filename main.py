# this file takes in the starting arguments for accessing the redis database.
# it parses them, and creates an object ('args') with these properties
# it then creates another object, 'myfunc', which is identical except that it also has a printargs function
# it then starts the flask app (the UI)
import re
import argparse
from flask import *
from tools.forms import PrimaryForm, BidForm, CapForm, StatusForm
from tools.functionality import Functionality, userInfo, yotamTime
from redis.exceptions import *


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

        if not request.method == 'POST':
            return render_template('base_home.html', form=form, step=0)

        else:  # if method == POST
            if len(request.form) == 3:  # if this is the first round

                if form.validate():
                    choice_name = dict(form.choice.choices).get(form.choice.data)
                    new_update.get_info(form.campaignID.data.strip(), form.dsp.data, form.choice.data, choice_name)
                    # the .strip() removes trailing spaces
                    myfunc.printargs(new_update.campaign_id)
                    myfunc.printargs(new_update.choice)
                    myfunc.printargs(new_update.DSP)

                    message = Markup('Attempting to update the %s for %s Campaign: <b>%s</b>') % \
                              (choice_name, new_update.DSP.title(), new_update.campaign_id)
                    flash(message)

                    if new_update.choice == "status":
                        form2 = StatusForm(request.form)
                        choice = form2.status
                    elif new_update.choice == "frequency_cap":
                        form2 = CapForm(request.form)
                        choice = form2.frequency_cap
                    else:
                        form2 = BidForm(request.form)
                        choice = form2.bid
                    return render_template('base_home.html', choice=choice, step=1)

                else:
                    flash('There was an issue with your input. Please try again.')
                    return render_template("base_home.html", form=form, step=0)

            else:
                # we need to search old_redis for the correct dict, and then the correct campaign_id, and then alter it
                old_redis = myfunc.getdoc(new_update.DSP)
                data = request.form.to_dict()

                if new_update.campaign_id not in old_redis[new_update.choice]:
                    flash("It looks like the campaign you're trying to update isn't in the algorithm. Please check all"
                          " of your parameters and try again.")
                    return render_template("base_home.html", form=form, step=0)

                else:
                    new_time = yotamTime()

                    if new_update.choice == 'status':

                        #store the old value
                        my_status = data['status']
                        if old_redis['status'][new_update.campaign_id] == True:
                            old_status = "Activated"
                        else:
                            old_status = "Paused"
                        new_update.get_oldvalue(old_status)

                        #update the redis over here
                        if my_status == 'Activated':
                            new_update.get_number(True)
                            old_redis['status'][new_update.campaign_id] = True
                        else:
                            new_update.get_number(False)
                            old_redis['status'][new_update.campaign_id] = False

                        #update time
                        old_redis['useruts'][new_update.campaign_id] = new_time

                    elif new_update.choice == 'frequency_cap':
                        try:
                            my_cap = float(data['frequency_cap'])

                            #validate not blank, whole number, set max and min
                            if data['frequency_cap'] and my_cap.is_integer() and my_cap > 0 and my_cap < 500:
                                new_update.get_number(my_cap)
                                #store the old value
                                old_cap = old_redis['frequency_cap'][new_update.campaign_id]
                                new_update.get_oldvalue(old_cap)

                                #update the new value
                                old_redis['frequency_cap'][new_update.campaign_id] = new_update.bid
                                old_redis['useruts'][new_update.campaign_id] = new_time

                            else:
                                form2 = CapForm(request.form)
                                choice = form2.frequency_cap
                                flash("Sorry, the frequency cap must be a whole number between 0 and 300")
                                return render_template("base_home.html", choice=choice, step=1)

                            #recreate the bid form
                        except ValueError:
                                form2 = CapForm(request.form)
                                choice = form2.frequency_cap
                                flash("Sorry, the cap you enter must be in integer form, e,g, 3")
                                return render_template("base_home.html", choice=choice, step=1)

                    else:
                        try:
                            my_bid = float(data['bid'])
                            if data['bid'] and my_bid > 0 and my_bid < 20:     #validating not blank, setting min/max
                                old_bid = old_redis[new_update.choice][new_update.campaign_id]
                                new_update.get_oldvalue(old_bid)

                                if new_update.choice == 'lowerbid':
                                    new_update.get_number(my_bid)
                                    old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                                elif new_update.choice == 'maxbid':
                                    new_update.get_number(my_bid)
                                    old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                                elif new_update.choice == 'bid':
                                    new_update.get_number(my_bid)
                                    old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                                old_redis['useruts'][new_update.campaign_id] = new_time

                            else:
                                form2 = BidForm(request.form)
                                choice = form2.bid
                                flash("Sorry, are you sure you entered a bid? It must be between 0 and 20.")
                                return render_template("base_home.html", choice=choice, step=1)

                        except ValueError:
                                form2 = BidForm(request.form)
                                choice=form2.bid
                                flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                                return render_template("base_home.html", choice=choice, step=1)

                    #update the redis
                    reply_value = old_redis[new_update.choice][new_update.campaign_id]

                    #update some terms for user message
                    new_update.get_name(old_redis['name'][new_update.campaign_id])
                    if new_update.choice == 'status':
                        if new_update.bid == False:
                            reply_value = 'Paused'
                        else:
                            reply_value = 'Activated'

                    try:
                        myfunc.mr.set_doc_by_dsp(new_update.DSP,old_redis)
                        form = PrimaryForm(request.form)
                        return render_template("base_home.html", term="successful", choice=new_update.choicename,
                                               id=new_update.name, oldbid=new_update.oldvalue, bid=reply_value,
                                               DSP=new_update.DSP, step=2, form=form)
                    except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
                        return render_template("algo_response.html", term=m, dog="/static/images/sad-dog.jpg")


    app.debug = False
    return app


if __name__ == '__main__':

    # create an object on the server and parse the args
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

    # instantiate two objects
    myfunc = Functionality(crdb, drdb, redisindex, redismastername,
                           redisipvec, esippush, esindnpush, timezone, log_level)

    new_update = userInfo()

    app = get_app(myfunc, new_update, "settings")
    app.run()