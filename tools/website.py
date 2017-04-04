import random
from flask import *
from .forms import PrimaryForm
from tools.forms import PrimaryForm, BidForm, CapForm, StatusForm


class FlaskApp(Flask):
    # app = Flask(__name__)
    # app.debug = True

    def __init__(self, *args, **kwargs):
        super(FlaskApp, self).__init__(*args, **kwargs)
        # self.complex_object = create_my_object()
    def setfunctions(self,myfunc,new_update):
        self.myfunc = myfunc
        self.new_update = new_update

    @app.route('/')
    def home(self):
        form = PrimaryForm(request.form)
        return render_template('base_home.html', form=form)

    @app.route('/update', methods=['GET', 'POST'])
    def update(self):
        print("yotam")
        form = PrimaryForm(request.form)
        form2 = StatusForm(request.form)
        form3 = CapForm(request.form)
        form4 = BidForm(request.form)
        if request.method == 'POST' and form.validate():
            flash('Your campaign ID is valid.')
            choice_name = dict(form.choice.choices).get(form.choice.data)
            self.new_update.get_info(form.campaignID._value(), form.DSP.data, choice_name)
            self.myfunc.printargs(self.new_update.campaign_id)
            self.myfunc.printargs(self.new_update.choice)
            self.myfunc.printargs(self.new_update.DSP)
            if self.new_update.choice == "Status":
                return render_template("status_home.html", form=form2, choice=self.new_update.choice, DSP=self.new_update.DSP,
                                       cam_id=self.new_update.campaign_id)
            elif self.new_update.choice == "Cap":
                return render_template("cap_home.html", form=form3, choice=self.new_update.choice, DSP=self.new_update.DSP,
                                       cam_id=self.new_update.campaign_id)
            else:
                return render_template("bid_home.html", form=form4, choice=self.new_update.choice, DSP=self.new_update.DSP,
                                       cam_id=self.new_update.campaign_id)
        else:
            return render_template('base_home.html', form=form)

    @app.route('/result', methods=['GET', 'POST'])
    def result(self):
        form2 = PrimaryForm(request.form)
        if request.method == 'POST':
            old_redis = self.myfunc.getdoc(self.new_update.DSP)
            if self.new_update.choice == 'Status':
                redis_info = request.form.getlist('status')
                new_redis = old_redis['status']
            elif self.new_update.choice == 'Cap':
                redis_info = request.form.getlist('cap')
            else:
                redis_info = request.form.getlist('bid')
            new_redis = old_redis, redis_info
            if random.random() > 0.5:  # instead of random, this will be - if response from server is positive, success; otherwise - failure
                return render_template("algo_response.html", term="a failure", dog="/static/images/sad-dog.jpg",
                                       doc=new_redis)
            else:
                return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg",
                                       doc=new_redis)
        else:
            flash('Sorry, your response wasn\'t valid. Please being the process again')
            return render_template("base_home.html", form=form2)

    # @app.route('/', methods=['GET'])
    # def home(self):
    #     self.form = PrimaryForm(request.form)
    #     if request.method == 'GET':
    #         return render_template("base_home.html", form=self.form)
    #
    # @app.route('/', methods=['POST', 'GET'])
    # def update(self):
    #     self.form = PrimaryForm(request.form)
    #     self.cam_id = self.form.campaignID._value()
    #     self.choice = self.form.choice.data
    #     self.choice_name = dict(self.form.choice.choices).get(self.form.choice.data)
    #     self.DSP = self.form.DSP.data
    #
    # @app.route('/update', methods=['POST'])
    # def submit(self):
    #     self.update()
    #     self.printer(self.cam_id)
    #     self.printer(self.choice)
    #     self.printer(self.DSP)
    #     self.bid = self.form.bid._value()
    #     self.printer(self.bid)
    #
    #     if self.form.validate():
    #         if self.choice == "status":
    #             return render_template("status_home.html", form=self.form, choice=self.choice_name, DSP=self.DSP,
    #                                    cam_id=self.cam_id)
    #         elif self.choice == "cap":
    #             return render_template("cap_home.html", form=self.form, choice=self.choice_name, DSP=self.DSP,
    #                                    cam_id=self.cam_id)
    #         else:
    #             return render_template("bid_home.html", form=self.form, choice=self.choice_name, DSP=self.DSP,
    #                                    cam_id=self.cam_id)
    #
    # @app.route('/result', methods=['POST'])
    # def result(self):
    #     if random.random() > 0.5:  # instead of random, this will be - if response from server is positive, success; otherwise - failure
    #         return render_template("algo_response.html", term="a failure", dog="/static/images/sad-dog.jpg")
    #     else:
    #         return render_template("algo_response.html", term="successful", dog="/static/images/happy-dog2.jpg")
    def runwev(self):
        self.app.run()


if __name__ == '__main__':
    UI = app(printargs)
