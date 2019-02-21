from flask_wtf import FlaskForm
from wtforms import SubmitField,  BooleanField 
import random

class MyBooleanField(BooleanField):
    pass



def file_list_form_builder(session,isdebug):
    class QuizForm(FlaskForm):
        pass

        
    rlist = session.quiz.Question().rsp
    x = [i for i in range( len(rlist) )]
    random.shuffle(x)
    
    for i in x:
        r = rlist[i]
        default = False 
        if isdebug:
            default = r.isright
        bf =  MyBooleanField(label=r.text,id =  str(r.id), default = default )
        setattr(QuizForm, 'r%02d' % i  , bf )

    setattr(QuizForm, 'submit', SubmitField('Наступне питання'))
    return QuizForm()


def rspids_from_form( form ):

    rids = []
    for field in form:
        if ( field.type == "MyBooleanField" ):
            if (field.data):
                rids.append ( int(field.id) )
                field.data = False

    return rids
 