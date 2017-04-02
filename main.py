#this file takes in the starting arguments for accessing the redis database.
# it parses them, and creates an object ('args') with these properties
#it then creates another object, 'myfunc', which is identical except that it also has a printargs function
# it then starts the flask app (the UI)
import re
import argparse
# from tools.website import myweb
# from tools.myweb2 import get_app
import random
from flask import *
from tools.forms import RegistrationForm, BidForm, CapForm, StatusForm
from tools.functionality import Functionality, userInfo

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

def get_app(myfunc,new_update,config_filename):
    app = Flask(__name__)
    # app.config.from_object(config_filename)
    app.config['SECRET_KEY'] = 'bx85EMx91xbf~8x8bxb3xfc!xe1xedxb6*xdeMxd7xeax06x9exda_'


    @app.route('/')
    def home():
        form = RegistrationForm(request.form)
        return render_template('base_home.html', form=form)
    @app.route('/update', methods=['GET', 'POST'])
    def update():
        print("yotam")
        form = RegistrationForm(request.form)
        form2 = StatusForm(request.form)
        form3 = CapForm(request.form)
        form4 = BidForm(request.form)
        if request.method == 'POST' and form.validate():
            flash('Your campaign ID is valid.')
            choice_name = dict(form.choice.choices).get(form.choice.data)
            new_update.get_info(form.campaignID._value(), form.DSP.data, choice_name)
            myfunc.printargs(new_update.campaign_id)
            myfunc.printargs(new_update.choice)
            myfunc.printargs(new_update.DSP)
            if new_update.choice == "Status":
                return render_template("status_home.html", form=form2, choice=new_update.choice, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)
            elif new_update.choice == "Cap":
                return render_template("cap_home.html", form=form3, choice=new_update.choice, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)
            else:
                return render_template("bid_home.html", form=form4, choice=new_update.choice, DSP=new_update.DSP,
                                       cam_id=new_update.campaign_id)
        else:
            return render_template('base_home.html', form=form)
    @app.route('/result', methods=['GET', 'POST'])
    def result():
        form2 = RegistrationForm(request.form)
        if request.method == 'POST':
            old_redis = myfunc.getdoc(new_update.DSP)
            if new_update.choice == 'Status':
                redis_info = request.form.getlist('status')
                new_redis = old_redis['status']
            elif new_update.choice == 'Cap':
                redis_info = request.form.getlist('cap')
            else:
                redis_info = request.form.getlist('bid')
            new_redis = old_redis[new_update.choice][new_update.campaign_id], redis_info
            if random.random() > 0.5:  # instead of random, this will be - if response from server is positive, success; otherwise - failure
                return render_template("algo_response.html", term="a failure", dog="/static/images/sad-dog.jpg", doc=new_redis)
            else:
                return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg", doc=new_redis)
        else:
            flash('Sorry, your response wasn\'t valid. Please being the process again')
            return render_template("base_home.html", form=form2)

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

    myfunc = Functionality(crdb, drdb, redisindex, redismastername, redisipvec, esippush, esindnpush, timezone, log_level)
    new_update = userInfo()

    app = get_app(myfunc,new_update,"settings")
    app.run()

# if __name__ == '__main__':
#     UI = app(printargs)