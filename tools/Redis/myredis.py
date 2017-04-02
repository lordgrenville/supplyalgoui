import ast
import decimal
import re
import sys
import time

from redis.sentinel import Sentinel
from redis.exceptions import *


class Transformer(ast.NodeTransformer):
    ALLOWED_NAMES = set(['Decimal', 'None', 'False', 'True'])
    ALLOWED_NODE_TYPES = set([
        'Expression', # a top node for an expression
        'Tuple',      # makes a tuple
        'Call',       # a function call (hint, Decimal())
        'Name',       # an identifier...
        'Load',       # loads a value of a variable with given identifier
        'Str',        # a string literal
        'NameConstant',
        'Num',        # allow numbers too
        'List',       # and list literals
        'Dict',       # and dicts...
    ])

    def visit_Name(self, node):
        if not node.id in self.ALLOWED_NAMES:
            raise RuntimeError("Name access to %s is not allowed" % node.id)

        # traverse to child nodes
        return self.generic_visit(node)

    def generic_visit(self, node):
        nodetype = type(node).__name__
        if nodetype not in self.ALLOWED_NODE_TYPES:
            raise RuntimeError("Invalid expression: %s not allowed" % nodetype)

        return ast.NodeTransformer.generic_visit(self, node)

def convert(data):
    if isinstance(data, bytes):  return data.decode('ascii')
    if isinstance(data, dict):   return dict(map(convert, data.items()))
    if isinstance(data, tuple):  return map(convert, data)
    return data

class demandlisttype:
    wf = "wid"
    tid = "tid"
class event:
    imp = "PUBLISHER_IMPRESSION"
    plyer_error = "VIDEO_PLAYER_ERROR"
    vast_timeout_code = "460"
    vpaid_timoeout_code = "560"
    view = "USER_VIEW"
    complete = "VIDEO_COMPLETE"
    viewable = "USER_VIEW_VIEWABLE_2_SEC"
    adopp = "AD_OPPORTUNITY"
    adrequest = "AD_REQUEST"
    adaveailable = "ADS_AVAILABLE"
    adwin = "AD_WIN"
    auction_error = "AUCTION_ERROR"
    dealerror = "DEMAND_ERROR"

class myredis:
    TimeOut = 10
    ipvec = []
    db=1
    sentinel = None
    slave=None
    master_name = ""
    basekey = "daily:event-counter:{0}:%d:%m:%Y:{1}:{2}:{3}"
    current_redies=None
    vid = "vid"
    def __init__(self,ipvec,index,master_name,drdb,crdb,TimeOut):
        self.index = index
        self.TimeOut = TimeOut
        self.ipvec = ipvec
        self.master_name = master_name
        self.drdb = drdb
        self.crdb = crdb
        self.sentinel = Sentinel(ipvec, socket_timeout=TimeOut)

    def ParseHashTable(self,dict):
        parsdoc = {}
        for item in dict.items():
            tid = re.split(":", item[0].decode())[-1]
            val = item[1]
            if val != None and int(val) > 0:
                parsdoc[tid] = int(val)
            else:
                parsdoc[tid] = int(0)
        return parsdoc

    def getimppertid(self):
        requestvec = {}
        impvec = {}
        try:
            slave = self.getSlave(1)
            impvals = slave.hgetall(time.strftime(self.basekey.format(self.index,event.imp,demandlisttype.tid,""))[0:-1])
            reqvals = slave.hgetall(time.strftime(self.basekey.format(self.index,event.adrequest,demandlisttype.tid,""))[0:-1])
        except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
            sys.exit("could not scan tids {0}".format(m))
        requestvec = self.ParseHashTable(reqvals)
        impvec = self.ParseHashTable(impvals)
        return impvec,requestvec

    def getSlave(self,db):
        try:
            slave = self.sentinel.slave_for(self.master_name ,socket_timeout = self.TimeOut,db = db)
            # slave = self.connect_to_stage(db)
        except:
            sys.exit("could not set a Slave DB - {db}".format(db = db))
        return slave

    def getmaster(self,db):
        try:
            if db!=1:
                master = self.sentinel.master_for(self.master_name ,socket_timeout = self.TimeOut,db = db)
                # master = self.connect_to_stage(db)
            else:
                sys.exit(1)
        except SystemExit as m:
            sys.exit("could not set a Slave DB - {db}".format(db = db))
        return master

    def Getset_doc_by_tag(self,tid,doc,subname):
        # _id ="RT" + tid
        _id = tid
        directory = "algo:{subname}:redistracking:tag:".format(subname=subname)+tid
        master = self.getmaster(self.drdb)
        try:
            doc = master.getset(directory,str(doc))
            # doc = master.getset("algo:test:redistracking:tag:"+tid,str(doc))
            if doc is None:
                doc ={}
        except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
            sys.exit("could not pull tagdoc-{tagid} from redis_m_{msg}".format(tagid = tid,msg=m))
        return convert(doc)

    def set_doc_by_dsp(self,dsp,doc):
        directory = "algo:{subname}:supplyopt:dspdoc:{dspname}".format(subname=self.index,dspname=dsp)
        master = self.getmaster(self.drdb)
        try:
            master.set(directory,str(doc))
        except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
            sys.exit("could not pull dspdoc-{dspname} from redis_m_{msg}".format(dspname = dsp,msg=m))

    def Get_doc_by_dsp(self,dsp):
        template = {
                    "bid": {},
                    "ecpm": {},
                    "name": {},
                    "lastupdatetime": {},
                    "status": {},
                    "lowerbid":{},
                    "clusters":{},
                    "activatets":{}
                }
        directory = "algo:{subname}:supplyopt:dspdoc:{dspname}".format(subname=self.index,dspname=dsp)
        slave = self.getSlave(self.drdb)
        try:
            doc = slave.get(directory)
            try:
                if bytes == type(doc):
                    dspdoc =  ast.literal_eval(convert(doc))
                else:
                    dspdoc = template
            except:
                tree = ast.parse(doc, mode='eval')
                transformer = Transformer()
                transformer.visit(tree)
                clause = compile(tree, '<AST>', 'eval')
                dspdoc = eval(clause, dict(Decimal=decimal.Decimal))
                # dspdoc = template
            for key in template.keys():
                if key not in dspdoc.keys():
                    dspdoc[key] = {}
        except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
            sys.exit("could not pull dspdoc-{dspname} from redis_m_{msg}".format(dspname = dsp,msg=m))
        return dspdoc

    def GetVidPerTid(self,TID):
        viddata = {}
        e=""
        try:
            slave = self.getSlave(self.crdb)
        except:
            sys.exit("could not set a Slave DB - {db}".format(db = self.db))
        try:
            e = "adopp_vid"
            viddata["adopp_vid"]= slave.hgetall(time.strftime(self.basekey.format(self.index, event.adopp, demandlisttype.tid, str(TID)))+":vid:exp")
            e = "adaveailable_vid"
            viddata["adaveailable_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.adaveailable, demandlisttype.tid, str(TID)))+":vid:exp")
            e = "adwin_vid"
            viddata["adwin_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.adwin, demandlisttype.tid, str(TID)))+":vid:exp")
            e = "view_vid"
            viddata["views_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.view, demandlisttype.tid, str(TID)))+":vid:exp")
            e = "viewable_vid"
            viddata["viewable_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.viewable, demandlisttype.tid, str(TID))) + ":vid:exp")
            e = "complete_vid"
            viddata["complete_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.complete, demandlisttype.tid, str(TID))) + ":vid:exp")
            e = "imp"
            imp = slave.hget(time.strftime(self.basekey.format(self.index,event.imp,demandlisttype.tid,""))[0:-1],str(TID))
            if None==imp:
                imp = 0
            else:
                imp = int(imp)
            e = "adrequest"
            adrequest = slave.hget(time.strftime(self.basekey.format(self.index,event.adrequest,demandlisttype.tid,""))[0:-1],str(TID))
            if None==adrequest:
                adrequest = 0
            else:
                adrequest = int(adrequest)
            e = "auction_error"
            auction_error = slave.hget(time.strftime(self.basekey.format(self.index, event.auction_error, demandlisttype.tid,""))[0:-1],str(TID))
            if None == auction_error:
                auction_error = 0
            else:
                auction_error = int(auction_error)
            e = "dealerror_vid"
            viddata["dealerror_vid"] = slave.hgetall(time.strftime(self.basekey.format(self.index, event.dealerror, demandlisttype.tid, str(TID))) + ":vid:exp")
            e = "vasterr_vid"
            viddata["vasterr_vid"] = slave.hgetall(time.strftime(str(self.basekey+":errc:{4}").format(self.index,
                                                                                                           event.plyer_error,
                                                                                                           demandlisttype.tid,
                                                                                                           str(TID),
                                                                                                           event.vast_timeout_code))+":vid:exp")
            e = "vperr_vid"
            viddata["vperr_vid"] = slave.hgetall(time.strftime(str(self.basekey+":errc:{4}").format(self.index,
                                                                                                           event.plyer_error,
                                                                                                           demandlisttype.tid,
                                                                                                           str(TID),
                                                                                                           event.vpaid_timoeout_code))+":vid:exp")
        except (ConnectionError,ResponseError,TimeoutError,WatchError,InvalidResponse) as m:
            sys.exit("could not pull {event} from redis_m_{msg}".format(event = e,msg=m))
        return adrequest,auction_error,imp,viddata

