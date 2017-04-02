from flask import *
import random
import re

from tools.forms import RegistrationForm, BidForm, CapForm, StatusForm

from tools.functionality import Functionality, userInfo

def get_app(myfunc,new_update,config_filename):
    app = Flask(__name__)
    # app.config.from_object(config_filename)
    # app.config['SECRET_KEY'] = 'bx85EMx91xbf~8x8bxb3xfc!xe1xedxb6*xdeMxd7xeax06x9exda_'


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
            new_redis = old_redis, redis_info
            if random.random() > 0.5:  # instead of random, this will be - if response from server is positive, success; otherwise - failure
                return render_template("algo_response.html", term="a failure", dog="/static/images/sad-dog.jpg", doc=new_redis)
            else:
                return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg", doc=new_redis)
        else:
            flash('Sorry, your response wasn\'t valid. Please being the process again')
            return render_template("base_home.html", form=form2)

    app.debug = False
    return app
