#this file takes in the starting arguments for accessing the redis database.
# it parses them, and creates an object ('args') with these properties
#it then creates another object, 'myfunc', which is identical except that it also has a printargs function
# it then starts the flask app (the UI)
import re
import argparse
from flask import *
from tools.forms import PrimaryForm, BidForm, CapForm, StatusForm
from tools.functionality import Functionality, userInfo

#parsing the init arguments for access to the redisDB
def parsing():
    parser = argparse.ArgumentParser(description='run the app')
    parser.add_argument('-cr','--crdb', dest="crdb", type=str)
    parser.add_argument('-dr', '--drdb', dest="drdb", type=str)
    parser.add_argument('-redind','--redisindex', dest="redisindex", type=str)
    parser.add_argument('-redmast','--redismastername', dest="redismastername", type=str)
    parser.add_argument('-redip','--redisipvec', dest="redisipvec", type=str)
    parser.add_argument('-esip', '--esippush', dest="esippush", type=str)
    parser.add_argument('-esind', '--esindnpush', dest="esindnpush", type=str)
    parser.add_argument('-tz', '--timezone', dest="timezone", type=str)
    parser.add_argument('-lvl', '--log_level', dest="log_level", type=str)
    args = parser.parse_args()
    return args

#this method initialises the flask app
def get_app(myfunc,new_update,config_filename):
    app = Flask(__name__)
    # app.config.from_object(config_filename)
    app.config['SECRET_KEY'] = 'bx85EMx91xbf~8x8bxb3xfc!xe1xedxb6*xdeMxd7xeax06x9exda_'

    #home view
    @app.route('/')
    def home():
        form = PrimaryForm(request.form)
        return render_template('base_home.html', form=form)

    #second view - the update view. this is one of three forms
    @app.route('/update', methods=['GET', 'POST'])
    def update():
        form = PrimaryForm(request.form)
        form2 = StatusForm(request.form)
        form3 = CapForm(request.form)
        form4 = BidForm(request.form)

        #if the form validates, go to one of three update views
        if request.method == 'POST' and form.validate():
            flash('Your campaign ID is valid.')
            choice_name = dict(form.choice.choices).get(form.choice.data)
            new_update.get_info(form.campaignID._value(), form.dsp.data, form.choice.data, choice_name)
            myfunc.printargs(new_update.campaign_id)
            myfunc.printargs(new_update.choice)
            myfunc.printargs(new_update.DSP)
            if new_update.choice == "status":
                return render_template("status_home.html", form=form2, choice=choice_name, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)
            elif new_update.choice == "frequency_cap":
                return render_template("cap_home.html", form=form3, choice=choice_name, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)
            else:
                return render_template("bid_home.html", form=form4, choice=choice_name, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)

        #if all else fails, go to the beginning view
        else:
            return render_template('base_home.html', form=form)

    #third view is result - we will tell the user if the Db has been successfully updated or not
    @app.route('/result', methods=['GET', 'POST'])
    def result():

        #initialise forms
        form = PrimaryForm(request.form)
        form2 = StatusForm(request.form)
        form3 = CapForm(request.form)
        form4 = BidForm(request.form)

        if request.method == 'POST':

            #we need to search old_redis for the correct dict, and then the correct campaign_id, and then alter it
            old_redis = myfunc.getdoc(new_update.DSP)

            #handle invalid input
            if not form3.validate() or not form4.validate():
                flash('Sorry, your response wasn\'t valid. Make sure that your bid or cap are in number form only (e.g.: 3.15 or 2). Please begin the process again')
                return render_template("base_home.html", form=form)

            else:
                if new_update.choice == 'status':
                    if form2.data['status'] == 'Activated':
                        old_redis['status'][new_update.campaign_id] = 1.0
                    else:
                        old_redis['status'][new_update.campaign_id] = 0.0

                elif new_update.choice == 'frequency_cap':
                    new_update.get_number(form3.data['frequency_cap'])
                    old_redis['frequency_cap'][new_update.campaign_id] = new_update.bid

                elif new_update.choice == 'lowerbid' or new_update.choice == 'maxbid' or new_update.choice == 'bid':
                    new_update.get_number(form4.data['bid'])
                    old_redis[new_update.choice][new_update.campaign_id] = new_update.bid

            #upload redis to server, get response, and based on that give either success or failure
                my_upload = myfunc.setdoc(new_update.DSP, old_redis)
                if my_upload == sys.exit:
                    return render_template("algo_response.html", term="not successful",
                                           dog="/static/images/sad-dog.jpg")
                else:
                return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg",
                                       choice=new_update.choicename, id=new_update.campaign_id,
                                       bid=old_redis[new_update.choice][new_update.campaign_id],
                                       redis=old_redis[new_update.choice])
    app.debug = False
    return app

if __name__ == '__main__':

    #create an object on the server and parse the args
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

    #instantiate two objects
    myfunc = Functionality(crdb, drdb, redisindex, redismastername,
                           redisipvec, esippush, esindnpush, timezone, log_level)

    new_update = userInfo()

    app = get_app(myfunc,new_update,"settings")
    app.run()