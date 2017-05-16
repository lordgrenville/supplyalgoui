from .Redis.myredis import myredis
import datetime
import time
import argparse

class Functionality:
    def __init__(self,crdb,drdb,redisindex,redismastername,redisipvec,esippush,esindnpush,timezone,log_level):
        self.crdb = crdb
        self.drdb = drdb
        self.redisindex = redisindex
        self.redismastername = redismastername
        self.redisipvec = redisipvec
        self.esippush = esippush
        self.esindnpush = esindnpush
        self.timezone = timezone
        self.log_level = log_level
        self.mr = myredis(ipvec=self.redisipvec,index=self.redisindex,master_name=self.redismastername,drdb=self.drdb,crdb=self.crdb,TimeOut=30)
        pass

    def printargs(self, x):
        print (self.drdb)
        print(x)

    def getdoc(self,dspname):
        doc = self.mr.Get_doc_by_dsp(dspname.lower())
        return doc

    def setdoc(self, dspname, doc):
        self.mr.set_doc_by_dsp(dspname.lower(),doc)

#this method gets a POSIX timestamp and formats it to have three trailing decimals
def yotamTime():
    # time in format YYYY-MM-DD HH:MM:SS.FFF
    t = str(datetime.datetime.fromtimestamp(time.time()))
    tail = t[-7:]
    f = round(float(tail),3)
    temp = "%.3f" % f
    return "%s%s" % (t[:-7], temp[1:])

#creating a dict of values to return to user
def information(redis_info, campaign_id):
        info = {'Name': redis_info['name'][campaign_id],
                'Status': redis_info['status'][campaign_id],
                'Bid': redis_info['bid'][campaign_id],
                'Maximum Bid': redis_info['maxbid'][campaign_id],
                'Minimum Bid': redis_info['lowerbid'][campaign_id],
                'Cap': int(redis_info['frequency_cap'][campaign_id])}

        # change the term for status from true/false to active/paused
        if info['Status'] == True:
            info['Status'] = "Active"
        else:
            info['Status'] = "Paused"
        return info

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

# validation: check for number by converting to float, check that input falls within given limits, optional additional
# check for integer (disabled by default)
def numberChecker(number, min, max, integer=False):
    try:
        n = float(number)
        if n > max or n < min:
            return "bad size"
        elif integer == True and n.is_integer() == False:
            return "bad input"
        else:
            return "good"
    except:
        return "bad input"

def update_algo(old_redis,session,curbid, maxbid, minbid, frequency_cap,status):
    # else request.form['submit'] is 'update', so create a dict to store form information
    options = {'bid': curbid, 'maxbid': maxbid, 'lowerbid': minbid, 'frequency_cap': frequency_cap, 'status': status}
    updates = {}
    oldvalues = {}
    
    # add form info to new_updates
    for x in options.keys():
        if options[x] != '':
            updates[x] = options[x]

    # search for each parameter and update it
    if 'status' in updates:
        # store the old value
        if old_redis['status'][session['campaign_id']] == True:
           oldvalues['status'] = "Activated"
        else:
            oldvalues['status'] = "Paused"

        # update the redis dict
        if updates['status'] == 'Activated':
            old_redis['status'][session['campaign_id']] = True
        else:
            old_redis['status'][session['campaign_id']] = False

    # ...and so on
    if 'frequency_cap' in updates:
        if numberChecker(updates['frequency_cap'], 0, 500) == "good":
            oldvalues['frequency_cap'] = old_redis['frequency_cap'][session['campaign_id']]
            old_redis['frequency_cap'][session['campaign_id']] = updates['frequency_cap']
        elif numberChecker(updates['frequency_cap'], 0, 500) == "bad size":
            message = "Sorry, the frequency cap must be a whole number between 0 and 300"
            return message
        else:
            message = "Unknown error. check your frequency cap is a number, e.g. 3"
            return message

    if 'bid' in updates:
        if numberChecker(updates['bid'], 0, 20) == "good":
            old_bid = old_redis['bid'][session['campaign_id']]
            oldvalues['bid'] = old_bid
            old_redis['bid'][session['campaign_id']] = updates['bid']
        elif numberChecker(updates['bid'], 0, 20) == "bad size":
            message = "Sorry, your bid must be between 0 and 20."
            return message
        else:
           message = "Sorry, the bid you enter must be in currency form, e,g, 3.45"
           return message

    if 'lowerbid' in updates:
        if numberChecker(updates['lowerbid'], 0, 20) == "good":
            old_bid = old_redis['lowerbid'][session['campaign_id']]
            oldvalues['lowerbid'] = old_bid
            old_redis['lowerbid'][session['campaign_id']] = updates['lowerbid']
        elif numberChecker(updates['lowerbid'], 0, 20) == "bad size":
            message = "Sorry, your bid must be between 0 and 20."
            return message
        else:
            message = "Sorry, the bid you enter must be in currency form, e,g, 3.45"
            return message

    if 'maxbid' in updates:
        if numberChecker(updates['maxbid'], 0, 20) == "good":
            old_bid = old_redis['maxbid'][session['campaign_id']]
            oldvalues['maxbid'] = old_bid
            old_redis['maxbid'][session['campaign_id']] = updates['maxbid']
        elif numberChecker(updates['maxbid'], 0, 20) == "bad size":
            message = "Sorry, your bid must be between 0 and 20."
            return message
        else:
            message = "Sorry, the bid you enter must be in currency form, e,g, 3.45"
            return message

    return old_redis, updates, oldvalues

def summary(updates, oldvalues):
    changes = []
    olds = []
    news = []
    for k, v in updates.items():
        if v != '':
            changes.append(k.title())
            olds.append(oldvalues[k])
            news.append(updates[k])
    rows = len(changes)
    return olds, news, changes, rows