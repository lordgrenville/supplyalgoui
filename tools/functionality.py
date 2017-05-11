from .Redis.myredis import myredis
import datetime
import time
import argparse

#this method gets a POSIX timestamp and formats it to have three trailing decimals
def yotamTime():
    # time in format YYYY-MM-DD HH:MM:SS.FFF
    t = str(datetime.datetime.fromtimestamp(time.time()))
    tail = t[-7:]
    f = round(float(tail),3)
    temp = "%.3f" % f
    return "%s%s" % (t[:-7], temp[1:])

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

class userInfo:
    def __init__(self):
        self.updates = {}
        self.oldvalues = {}
    def get_info(self, campaign_id,  DSP):
        self.campaign_id = str(campaign_id)
        self.DSP = str(DSP)
    def get_name(self, name):
        self.name = name