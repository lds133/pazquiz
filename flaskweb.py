#!/usr/bin/python3

from flask import Flask, render_template, url_for, flash, redirect,request
from session import Session
from quiz import Quiz, QuizCFG, QuizDB
import forms




QuizCFG.ISDEBUG = False


app = Flask(__name__)

app.config['SECRET_KEY'] = 'DEBUG'

ERROR_TOOMANY_SESSIONS_OPENNED = 100
ERROR_SESSION_ID_NOT_FOUND = 101
ERROR_SESSION_ERROR = 102


QuizDB.Instance()


@app.route("/")
@app.route("/h")
def home():
    return render_template('home.html', quizdb = QuizDB.Instance() )

    

#@app.route("/a")
@app.route("/myextremelysecureadminpage")
def admin():
    return render_template(     'admin.html',
                                title='Admin', 
                                quizdb = QuizDB.Instance(), 
                                report = Session.ToHTML( None, Session.ReportText())   ,
                                QuizCFG = QuizCFG )
    
@app.route("/n")
def new():
    Session.KillOld()
    if (not Session.CheckCount()):
        return render_template('error.html', title='Error', quizdb = QuizDB.Instance(), errcode = ERROR_TOOMANY_SESSIONS_OPENNED)

    s = Session( str( request.remote_addr ) )
    return redirect( url_for('quiz',sid = s.sid) )

    
    
  
@app.route("/q/<sid>",methods=['post','get'])
def quiz(sid):
    s = Session.Get(sid) 
    if (s==None):
        return render_template('error.html', title='404', quizdb = QuizDB.Instance(),errcode = ERROR_SESSION_ID_NOT_FOUND, errortext = sid)
    f = forms.file_list_form_builder(s,QuizCFG.ISDEBUG)
   
    if f.validate_on_submit():
        rids = forms.rspids_from_form( f )
        if (len( rids) != 0 ):
            rc = s.quiz.Answer( rids )
            if (rc != Quiz.OK):
                return redirect( url_for('result',sid = s.sid) )
            return redirect( url_for('quiz',sid = s.sid) )
    
    return render_template('question.html', form=f , title='Quiz', quizsession = s, quizdb = QuizDB.Instance())
    

@app.route("/r/<sid>")
def result(sid):
    s = Session.Get(sid)   
    if (s==None):
        return render_template('error.html', title='404', quizdb = QuizDB.Instance(), errcode = ERROR_SESSION_ID_NOT_FOUND, errortext = sid)
    if (s.quiz.state != Quiz.DONE):
        s.Kill()
        return render_template('error.html', title='Error', quizsession = s, quizdb = QuizDB.Instance(), errcode = ERROR_SESSION_ERROR )
    else:
        s.Save()
        s.Kill()
        return render_template('result.html', title='Result', quizsession = s, quizdb = QuizDB.Instance())
    

   
    
if __name__ == '__main__':
    Session.CleanUp()
    app.run(debug=QuizCFG.ISDEBUG, host='0.0.0.0')
    