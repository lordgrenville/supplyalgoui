# this file takes in the starting arguments for accessing the redis database.
# it parses them, and creates an object ('args') with these properties
# it then creates another object, 'myfunc', which is identical except that it also has a printargs function
# it then starts the flask app (the UI)
import re
import argparse
from flask import *
from tools.forms import PrimaryForm, BidForm, CapForm, StatusForm
from tools.functionality import Functionality, userInfo


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
    app.config['SECRET_KEY'] = 'bx85EMx91xbf~8x8bxb3xfc!xe1xedxb6*xdeMxd7xeax06x9exda_'

    # home view
    @app.route('/', methods=['GET', 'POST'])
    def home():
        form = PrimaryForm(request.form)

        if request.method == 'GET':
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

                    message = Markup('Your campaign ID is valid.You are updating the %s for %s Campaign: <b>%s</b>') % \
                              (choice_name, new_update.DSP, new_update.campaign_id)
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
                # validate forms!
                    if new_update.choice == 'status':

                        my_status = data['status']
                        if my_status == 'Activated':
                            old_redis['status'][new_update.campaign_id] = 1.0
                        else:
                            old_redis['status'][new_update.campaign_id] = 0.0

                    elif new_update.choice == 'frequency_cap':
                        my_cap = data['frequency_cap']
                        try:
                            float(my_cap)
                            new_update.get_number(my_cap)
                            old_redis['frequency_cap'][new_update.campaign_id] = new_update.bid

                        #recreate the bid form
                        except:
                            ValueError
                            form2 = CapForm(request.form)
                            choice = form2.frequency_cap
                            flash("Sorry, the cap you enter must be in integer form, e,g, 3")
                            return render_template("base_home.html", choice=choice, step=1)

                    else:
                        my_bid = data['bid']

                        try:
                            float(my_bid)

                            if new_update.choice == 'lowerbid':
                                new_update.get_number(my_bid)
                                old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                            elif new_update.choice == 'maxbid':
                                new_update.get_number(my_bid)
                                old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                            elif new_update.choice == 'bid':
                                new_update.get_number(my_bid)
                                old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

                        except ValueError:
                            form2 = BidForm(request.form)
                            choice=form2.bid
                            flash("Sorry, the bid you enter must be in currency form, e,g, 3.45")
                            return render_template("base_home.html", choice=choice, step=1)

                    return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg",
                                               choice=new_update.choicename, id=new_update.campaign_id,
                                               bid=old_redis[new_update.choice][new_update.campaign_id],
                                               redis=old_redis[new_update.choice])

    app.debug = True
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