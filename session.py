import datetime
import html
from threading import Lock
from quiz import QuizDB,QuizCFG
import random




class Session():
    counter = 0
    lock = Lock()
    list = dict()
    lastkilltime = None
    KILLCHECKTIMEMINS = 1
   
    
    
    sid = None
    quiz = None
    ip = None
    timestamp = None
    
    
    def __init__(self,clientip):
        Session.lock.acquire()
        while True:
            self.sid = "%08X" % random.randint(0, 0xFFFFFFFF) #uuid.uuid4().hex #str(Session.counter)
            if (not (self.sid in Session.list)):
                break
        Session.counter += 1
        Session.list[self.sid] = self
        Session.lock.release()
        self.quiz = QuizDB.Instance().MakeNewQuizQuestionSet(QuizCFG.QUESTIONSCOUNT)
        self.ip = clientip
        self.timestamp = datetime.datetime.now()
        print("Session %s opened" % self.sid);
        

    def Get(sid):
        s = None;
        Session.lock.acquire()
        if sid in Session.list:
            s = Session.list[sid]
        Session.lock.release()
        return s


        
    def CleanUp():
        Session.lock.acquire()
        Session.counter=1 
        Session.list.clear();
        Session.lock.release()
        
        
    def KillOld():
        if (Session.lastkilltime!=None):
            dtmins = (datetime.datetime.now() - Session.lastkilltime).total_seconds() / 60.0
            if (dtmins<Session.KILLCHECKTIMEMINS):
                return
        Session.lock.acquire()
        victims = []
        for (k,v) in Session.list.items():
            #print(">>> kill %s %s"+ str(k)+ str(v.AgeInMins()))
            if (v.AgeInMins()>QuizCFG.SESSIONTIMEMINS):
                victims.append( k )
        for k in victims:
            Session.list.pop(k , None)
        Session.lock.release()
        
        Session.lastkilltime = datetime.datetime.now()
        pass
        
        
    def ReportText():
        db = QuizDB.Instance()
        Session.lock.acquire()
        txt = ""
        txt+= "uptime = %s\r\n" % str( datetime.datetime.now() - db.timestamp)
        txt+= "session counter = %i\r\n" % Session.counter
        txt+= "db key = '%s'\r\n" % db.key
        txt+= "db version  = '%s'\r\n" % db.version
        txt+= "db date  = '%s'\r\n" % db.date
        txt+= "db timestamp  = '%s'\r\n" % str(db.timestamp)
        if (len(Session.list)==0):
            txt+= "No sessions opened\r\n"
        else:
            txt+= "Sessions:\r\n"
            for (k,v) in Session.list.items():
                age = datetime.datetime.now() - v.timestamp
                txt+= " '%s' at %i, %s, %s, %s\r\n" % ( k, v.quiz.pos, str(v.quiz.state), str(age), v.ip )
        Session.lock.release()
        
        return txt
        
        
    
        
    def CheckCount():
        Session.lock.acquire()
        n = len( Session.list )
        Session.lock.release()
        return (n <  QuizCFG.MAXSESSIONSCOUNT)
        
        
    def TotalCount(self):
        Session.lock.acquire()
        n = len( Session.list )
        Session.lock.release()
        return n
        
    def Save(self):
        self.quiz.Save( QuizDB.Instance().dir+("/%s.txt" % self.sid)  ,  "Client ip: %s"  %  self.ip )
        
    def Kill(self):
        Session.lock.acquire()
        Session.list.pop(self.sid, None)
        Session.lock.release()
        print("Session %s closed" % self.sid);
        pass
        
        
    def ToHTML(self,text):
        return  html.escape(text).replace("\n","<br>");
        
    def AgeInMins(self):
        dtmins = (datetime.datetime.now() - self.timestamp).total_seconds() / 60.0
        return int(dtmins)
        
        
        
    def MinsLeft(self):
        return QuizCFG.SESSIONTIMEMINS - self.AgeInMins() 
    
        