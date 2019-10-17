from app import app
from flask import flash, redirect, render_template, request, session, url_for, jsonify
from functools import wraps
from app.forms import RegisterForm, LoginForm, SearchForm
import sys
#from app.models import User
import config
import os
import stripe
import tweepy
import json
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import pyrebase
import numpy as np

app.config.from_pyfile('keys.cfg')
stripe_keys = {
    'secret_key': app.config['SECRET_KEY'],
    'publishable_key': app.config['PUBLISHABLE_KEY']
}
stripe.api_key = stripe_keys['secret_key']


auth = tweepy.OAuthHandler(config.consumer_key, config.consumer_secret)
auth.set_access_token(config.access_token, config.access_token_secret)
api = tweepy.API(auth)

sid = SentimentIntensityAnalyzer()


firebase = pyrebase.initialize_app(config.firebaseConfig)
# Get a reference to the auth service
auth = firebase.auth()
# Get a reference to the database service
db = firebase.database()


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,error), 'error')

def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

def payment_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        
        if check_payment():        
            return test(*args, **kwargs)
            
        flash('You need to pay to access this')
        return redirect(url_for('members'))
    return wrap

def check_payment():
    all_users = db.child("users").get()
    users = []
    for user in all_users.each():
        users.append(user.val())
    
    for user in users:
        if user['email'] == session['user_email']:
            return (user['paid'])
    return False
    

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.pop('user_email', None)
    flash('You are logged out. Bye. :(')
    return redirect (url_for('login'))

@app.route('/')
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method=='POST':
        # Log the user in
        #authenticate a user
        try:
            user = auth.sign_in_with_email_and_password(request.form['email'], request.form['password'])
            session['id_token'] = user['idToken']
        except:
            flash("wrong credentials")
            return render_template("login.html",
                            form = LoginForm(request.form),
                            error = error)

        if user is None:
            error = 'Invalid username or password.'
        else:
            session['logged_in'] = True
            session['user_email'] = user['email']
            
            flash('You are logged in. Go Crazy.')
            return redirect(url_for('members'))

    return render_template("login.html",
                            form = LoginForm(request.form),
                            error = error)

@app.route('/members/')
@login_required
def members():
    if check_payment():
        flash("you paid, now you play")
        return redirect(url_for('search'))
    return render_template('members.html', key=stripe_keys['publishable_key'])


@app.route('/search', methods=['GET','POST'])
@login_required
@payment_required
def search():
    error = None
    if request.method =='POST':
        if request.method == 'POST':
            search_tweet = request.form['search_term']
            t = []
            scores = []
            max_tweets = 100
            for tweet in tweepy.Cursor(api.search, q=search_tweet).items(max_tweets):
                text = tweet._json["text"]
                ss = sid.polarity_scores(text)
                t.append({'text': text, 'score': ss["compound"]})
                scores.append(ss["compound"])
            average_score = np.average(scores)
            tweets = t
            return render_template('search.html', tweets=tweets, average=average_score,form=SearchForm(request.form))
    return render_template('search.html', form=SearchForm(request.form))

@login_required
@app.route('/charge', methods=['POST'])
def charge():
    try:
        # Amount in cents
        amount = 600
        email = session['user_email']

        customer = stripe.Customer.create(
            email=email,
            card=request.form['stripeToken']
        )

        charge = stripe.Charge.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description='Flask Charge'
        )
        db = firebase.database()
        session['paid'] = True
        data = {'email':email, 'paid': True, 'idToken': session['id_token']}
        db.child("users").update(data)

        return render_template('charge.html', amount=amount)
    except:
        flash('Charge error, try again')
        return redirect(url_for('members'))

@app.route('/register/', methods=['GET','POST'])
def register():
    error = None
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        try:
            '''db.session.add(new_user)
            db.session.commit()'''
            user = auth.create_user_with_email_and_password(form.email.data, form.password.data)
            auth.get_account_info(user['idToken'])
            data = {'email':form.email.data, 'paid': False}
            db.child("users").update(data)
            flash('Thanks for registering. Please login.')
            return redirect(url_for('login'))
        except IntegrityError:
            error = 'Oh no! That username and/or email already exist. Please try again.'
    else:
        flash_errors(form)
    return render_template('register.html', form=form, error=error)

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404