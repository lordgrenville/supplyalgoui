from .Redis.myredis import myredis
import datetime
import time

def yotamTime():
    # time in format YYYY-MM-DD HH:MM:SS.FFF
    t = str(datetime.datetime.fromtimestamp(time.time()))
    tail = t[-7:]
    f = round(float(tail),3)
    temp = "%.3f" % f
    return "%s%s" % (t[:-7], temp[1:])

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
        self.campaign_id = None
        self.DSP = None
        self.choice = None
    def get_info(self, campaign_id,  DSP, choice, choicename):
        self.campaign_id = str(campaign_id)
        self.DSP = str(DSP)
        self.choice = str(choice)
        self.choicename = choicename
    def get_number(self, bid):
        self.bid = float(bid)
    def get_oldvalue(self, value):
        self.oldvalue = value
    def get_name(self, name):
        self.name = name