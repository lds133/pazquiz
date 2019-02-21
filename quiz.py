import xml.etree.ElementTree as ET
import uuid
import os
import datetime
import random
from enum import Enum


#not thread safe !

  
class QuizCFG():
    HOMEPROJECTURL = "https://github.com/"
    VERSION = "1.0.0"
    XMLFILE =  "data/dummy_questions.xml"
    TMPDIR = "tmp/"
    TEXTFILENAME = "questions.txt"
    QUIZGROUPSCOUNT = 2 # todo: calculate from xml file
    QUESTIONSCOUNT = 4
    ISDEBUG = False
    SESSIONTIMEMINS = 60
    MAXSESSIONSCOUNT = 100    
   


class Quiz(Enum):
   OK = 1
   DONE = 2
   ERROR = 100
   ERROR_NOMOREQUESTIONS = 101
   ERROR_WRONGRESPONCEID = 102
   ERROR_NORESPONCES = 103
   ERROR_TOOMANYRESPONCES = 104
   ERROR_WRONGRESPONCES = 105
   



class QuizQuestionSet():


    class QQSet():
        question = None
        isright = False
        answerids = None
        answertime = None

        def __init__(self,question):
            self.question = question 
            
        def SetAnswer(self,isright,answerids):
            self.isright = isright
            self.answerids = answerids
            self.answertime = datetime.datetime.now()
        
        

    TOOFAR = 9999
        
    data = None
    pos = 0
    state = None
    starttime = None
    stoptime = None
    
    
    def __init__(self):
        self.data = []
        self.pos = 0
        self.state = Quiz.OK
        
        
        
    
    def Size(self,group=None):
        if (group==None):
            return len(self.data)
        else:            
            return sum(qq.question.group == group for qq in self.data)
        
    def Add(self, question):
        #sameid = sum(qq.question.id == question.id for qq in self.data)
        self.data.append( QuizQuestionSet.QQSet( question ) )
       
       
    def Distance(self,questionid):
        min = self.TOOFAR
        for qq in self.data:
            d = abs(qq.question.id - questionid )
            if (d<min):
                min = d
        return min
       
       
    def Question(self):
        if (self.pos>=self.Size()):
            return None
        if (self.state != Quiz.OK):
            return None
        
        if (self.starttime==None):
            self.starttime = datetime.datetime.now()
            
        return self.data[ self.pos ].question
    
       
    def Answer(self, respidlist ):
        if (self.state == Quiz.ERROR):
            return Quiz.ERROR
    
        if (self.pos>=self.Size()):
            #print("ERROR_NOMOREQUESTIONS")
            return Quiz.ERROR_NOMOREQUESTIONS
        if (len(respidlist)==0):
            #print("ERROR_NORESPONCES");
            return Quiz.ERROR_NORESPONCES
        s = self.data[ self.pos ]
        
        ids = list(set(respidlist))
        if (len(ids)>len(s.question.rsp)):
            self.state = Quiz.ERROR
            #print("ERROR_TOOMANYRESPONCES")
            return Quiz.ERROR_TOOMANYRESPONCES
        
        rightcount = 0
        wrongcount = 0
        for r in s.question.rsp:
            if (ids.count(r.id) > 0):
                ids.remove( r.id )
                if (r.isright):
                    rightcount+=1
                else:
                    wrongcount+=1
            
        isright = (rightcount == s.question.rightrspcount) and (wrongcount == 0)
        
        
        if (len(ids)!=0):
            self.state = Quiz.ERROR
            #print("ERROR_WRONGRESPONCES",ids)
            return Quiz.ERROR_WRONGRESPONCES
        
        s.SetAnswer( isright,respidlist )

        self.pos+=1
        
        if (self.pos>=self.Size()):
            self.state = Quiz.DONE
            self.stoptime = datetime.datetime.now()
            return Quiz.DONE
            
        return Quiz.OK
        
    def RightAnswersCount(self):
        if (self.state != Quiz.DONE):
            return 0
        return  sum( (s.isright) for s in self.data ) 
        
    def TotalAnswersCount(self):
        return  len( self.data )    

    def Position(self):     
        return (self.pos+1)
        
    def Save(self,filename,exttextline):
        if (self.state != Quiz.DONE):
            return     

        file = open(filename,'w', encoding='cp1251') 
        file.write(exttextline)
        file.write("\r\n")
        file.write("Start: " + str(self.starttime) +"\r\n")
        file.write("Duration: " + str(self.stoptime - self.starttime) +"\r\n")

        t = self.starttime
        for s in self.data:
            c = None
            if (s.isright):
                c = "+" 
            else:
                c = "-"
            dt = s.answertime - t  
            t = s.answertime
            file.write( "%s:%04i " % (c,s.question.id) )
            file.write( str(dt) )
            file.write( " " )
            file.write( str( s.answerids ) ) 
            file.write("\r\n") 

        
        file.close()
        pass
        
    

class QuizResponce():

    id = None
    parent = None
    isright = None
    text = None
    
    def __init__(self,question,xmlelement):
        self.id = QuizDB.GetUniqueIndex()
        self.parent = question
        self.Fill(xmlelement)

    def Fill(self,e):
        self.isright = (e.attrib['isright'].lower() == 'true')
        et = e.find('text');
        if (et==None) or (et.text==None) or (et.text==""):
            print("XML warning: no text for responce %s" % self.id)
        else:
            self.text = et.text

        
        

class QuizQuestion():
    
    id = None
    group = None
    text = None
    img = None
    code = None
    rsp = None
    rightrspcount = None
    
    def __init__(self,xmlelement):
        self.id = QuizDB.GetUniqueIndex()
        self.Fill(xmlelement)
        
    def Fill(self,e):
        self.group = e.attrib['group']

        self.text = None
        for t in e.findall('text'):
            if (t.text!=None):
                self.text = t.text.strip("\r\n\t ")
        if (self.text==None):
            print("XML warning: no text for question %s" % self.id)

        self.img = None
        for i in e.findall('img'):
            if (i.text!=None):
                self.img =  i.text.strip("\r\n\t ")
                
        self.code = None
        for i in e.findall('code'):
            if (i.text!=None):
                self.code =  i.text.strip("\r\n\t ")
        
        responces = e.find('responces')
        
        if (responces==None):
            print("XML warning: no responces for '%s'" % self.text)
            return
        
        self.rsp = []
        self.rightrspcount = 0
        for child in responces:
            if (child.tag != 'r'):
                continue
            r = QuizResponce(self,child)
            if (r.isright):
                self.rightrspcount+=1
            self.rsp.append(r)






class QuizDB():

    counter = 1
    def GetUniqueIndex():
       n = QuizDB.counter
       QuizDB.counter += 1
       return n

   

    instance = None

    def Instance():
      if (QuizDB.instance == None):
         QuizDB()
      return QuizDB.instance
      
    def __init__(self):
      if (QuizDB.instance != None):
         raise Exception("Quiz is a singleton!")
      else:
         QuizDB.instance = self
         self.Load(QuizCFG.XMLFILE)
         self.SaveTXT()

         
    ql = None
    version = None
    date = None
    key = None
    dir = None
    xmlfilename = None
    timestamp = None
   
    def Load(self, xmlfilename):
        self.timestamp = datetime.datetime.now()
        self.xmlfilename = xmlfilename
        tree = ET.parse(xmlfilename)
        root = tree.getroot()
        self.version = root.attrib['version']
        self.date = root.attrib['date']
        print("XML loaded '%s' ver %s, date %s" % (xmlfilename,self.version,self.date))
        
        
        if (QuizCFG.ISDEBUG):
            self.key = 'debug' 
        else:
            #self.key = uuid.uuid4().hex
            self.key = str(self.timestamp).replace(':', '_').replace(' ', '_').replace('.', '_').replace('-', '_')
        
        print("XML key is '%s'" % (self.key))
        self.dir = QuizCFG.TMPDIR + self.key
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
        
        filelist = [ f for f in os.listdir(self.dir) ]
        for f in filelist:
            os.remove(os.path.join(self.dir, f))
        
        questions = root.find('questions')
        if (questions==None):
            raise Exception("XML No questions found!")
            
        self.ql = dict()
        for child in questions:
            if (child.tag != 'q'):
                continue
            q = QuizQuestion(child)
            self.ql[q.id] = q
            
        print("XML %i questions found" % len(self.ql))
        
        
            

        
        
    def SaveTXT(self):
        fn = self.dir + "/" + QuizCFG.TEXTFILENAME
        file = open(fn,'w', encoding='cp1251') 
        
        file.write("%s\r\n" % str(self.timestamp) )
        file.write("XML file '%s' ver %s, date %s" % (self.xmlfilename,self.version,self.date))
        file.write("\r\n\r\n\r\n")
        
        for k,v in self.ql.items():
            file.write('%4s: %s' % (str(k),v.text));
            if (v.img!=None):
                file.write('      %s' % v.img);
            if (v.code!=None):
                file.write('      %s' % v.code);
            file.write("\r\n");
            for r in v.rsp:
                c = "    "
                if (r.isright):
                    c = "--->"
                file.write('%s%4s: %s\r\n' % (c,str(r.id),r.text));
                
                
            file.write('\r\n\r\n');
            
        file.close()
        
        
    def MakeNewQuizQuestionSet(self, questionscount):
        
        
        data = list( self.ql.values() )
        size = len( data ) - 1
        quiz = QuizQuestionSet()
        fusecounter = 0
        BLOWFUSE = 9999
        
        
        if False:#(QuizCFG.ISDEBUG):
        
            quiz.Add( self.ql[1238] )
            quiz.Add( self.ql[537] )
            quiz.Add( self.ql[584] ) 
        
        else:        
            pos = 0
            while (quiz.Size()<questionscount):
                
                if (fusecounter>BLOWFUSE):
                    #error
                    break
                
                pos = random.randint(0,size)
                q = data[pos]
                
                distance = quiz.Distance(q.id)
                
                if (distance==0):
                    fusecounter+=1
                    continue

                if (distance<=3):
                    if (random.random()>0.5):
                        fusecounter+=1
                        continue
                    
                if (distance==1):
                    if (random.random()>0.2):
                        fusecounter+=1
                        continue

                if ( quiz.Size( q.group ) > ((questionscount/QuizCFG.QUIZGROUPSCOUNT)+1) ):
                    fusecounter+=1
                    continue
                
                quiz.Add( data[pos] )
            
        
        
        quiz.data.sort(key=lambda x: (x.question.group,x.question.id), reverse=False)
        
        
        #for (i,qq) in enumerate(quiz.data):
        #    print("%i) %s %s" % (i,qq.question.group,qq.question.id)) 
        #print("Fuse %i" % (fusecounter)) 
        
        return quiz;
        
        
        
    def Test(self):
    
        sessionid = 123
    
        quiz = self.MakeNewQuizQuestionSet(20)

        print(quiz.Question().text)
        
        rc = quiz.Answer([3,4])
        print(rc)

        rc = quiz.Answer([7])
        print(rc)

        rc = quiz.Answer([46,47])
        print(rc)

        print("-->"+ str(quiz.state) + " "+str(quiz.RightAnswersCount()))
        
        
        for s in quiz.data:
            print("%s - %s" % (s.question.id, s.question.group));
            
            
        quiz.Save(self.dir+("/%08i.txt" % sessionid))

        print("test!")

    def GetCFG(self,name):
        return getattr(QuizCFG, name)
   

   
   
   
if __name__ == '__main__':



    QuizDB.Instance().Test()
    
         

         