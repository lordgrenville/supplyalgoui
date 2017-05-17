import re
from flask import *
from tools.forms import PrimaryForm
from tools.functionality import Functionality, yotamTime, information, parsing, update_algo, summary


# initialise a flask object, and call the run method. this will start our site!
def get_app(myfunc):
    app = Flask(__name__)
    # setting a secret key in the config dict - this is needed so that we can flash messages
    app.secret_key = 'os.urandom(24)'

    # handle crash in rendering page - this way the app won't crash if one page does
    def rendering(html,**kwargs):
        try:
            return render_template(html,**kwargs)
        except SystemExit:
            abort(404)

    # generic error handling
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('algo_fail_response.html'), 404

    @app.route('/', methods=['GET','POST'])
    def home():

        form = PrimaryForm(request.form)
        if request.method == 'GET':
            return rendering('base_home.html', form=form, step=0)

        # check campaign ID exists
        if form.campaignID.data == '':
            flash('You didn\'t enter a campaign ID!')
            return rendering("base_home.html", form=form, step=0)

        # store campaign ID and DSP in session, strip trailing spaces
        session['campaign_id'] = form.campaignID.data.strip()
        session['dsp'] = form.dsp.data

        # we need to search old_redis for the correct dict, and then the correct campaign_id, and then alter it
        try:
            old_redis = myfunc.getdoc(session['dsp'])
        except SystemExit as m:
            return rendering("algo_fail_response.html", error=m)

        if session['campaign_id'] not in old_redis['status']:
            flash("It looks like the campaign you're trying to update isn't in the algorithm. Please check all"
                  " of your parameters and try again.")
            return rendering("base_home.html", form=form, step=0)

        try:
            session['name'] = old_redis['name'][session['campaign_id']]
        except SystemExit:
            return rendering("algo_fail_response.html")

        if form.get_info.data:
            # if 'update' selected, get all of the old data and store it in a dict
            info = information(old_redis,session['campaign_id'])
            return rendering("base_home.html", info=info, DSP=session['dsp'], id=session['name'], form=form,
                                   step=1, rows=0)

        # else if request.form['submit'] is 'update', create a dict to store form information
        elif form.update.data:
            old_redis, updates, values, message =  update_algo(old_redis, session, form.curbid.data, form.maxbid.data,
                            form.minbid.data, form.frequency_cap.data, form.status.data)

            # if this returns a message, not a tuple, flash it and go back
            if len(message) > 0:
                flash(message)
                return rendering('base_home.html', form=form, step=0)

            else:
                # update the userts (timestamp)
                new_time = yotamTime()
                old_redis['useruts'][session['campaign_id']] = new_time

                # save info for old and new values in dicts to display to the user
                olds, news, changes, rows= summary(updates, values)

                # return landing page to user with success/failure message
                try:
                    myfunc.mr.set_doc_by_dsp(session['dsp'], old_redis)
                    return rendering("base_home.html", id=session['name'], DSP=session['dsp'].title(),
                                           changes=changes, rows=rows, olds=olds, news=news, step=2, form=form)
                except SystemExit as m:
                    return rendering("algo_fail_response.html")

    app.debug = False
    return app


if __name__ == '__main__':

    # instantiate parser
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

    # instantiate a class called myfunc to store stuff
    myfunc = Functionality(crdb, drdb, redisindex, redismastername,
                           redisipvec, esippush, esindnpush, timezone, log_level)
    try:
        app = get_app(myfunc)
        app.run(debug=True, use_debugger=False, use_reloader=False)
    except:
        pass