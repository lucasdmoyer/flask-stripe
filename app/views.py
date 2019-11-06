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
import pandas as pd
from keras.models import model_from_json
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.layers import Embedding
from keras.layers import LSTM
from keras.models import load_model
import time
import requests
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.layers import Dense, Activation
from sklearn.model_selection import train_test_split
from yahoofinancials import YahooFinancials
from pandas_datareader import data
from flask_googlecharts import GoogleCharts
from flask_googlecharts import LineChart, BarChart
from flask import Flask
from flask_googlecharts import GoogleCharts





from app.model import load
#global vars for easy reusability
global model
#initialize these variables
model = load.init()

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
        if str(user['email']) == str(session['user_email']):
            return (user['paid'])
    return False

def convert_time(epoch):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch))
    
def get_stocks():
    ####### STOCKS
    epoch_time = int(time.time())
    day_epoch = 60*60*24
    aapl = data.DataReader("AAPL", 
                        start=convert_time(epoch_time - (1000* day_epoch)), 
                        end=convert_time(epoch_time), 
                        data_source='yahoo')
    aapl = aapl.reset_index()
    X = aapl[['High', 'Low', 'Open', 'Volume']].values
    Y = aapl[['Close']].values
    # normalize the dataset
    X_scaler = MinMaxScaler(feature_range=(0, 4))
    X_scaled_dataset = X_scaler.fit_transform(X)

    Y_scaler = MinMaxScaler(feature_range=(0,1))
    Y_scaled_dataset = Y_scaler.fit_transform(Y)
    X_set =[]
    Y_set = []

    for i in range(50, len(X_scaled_dataset)):
        X_set.append(X_scaled_dataset[i-50:i] )
        Y_set.append(Y_scaled_dataset[i] )
        
    X_array = np.array(X_set)
    Y_array = np.array(Y_set)

    X_reshape = X_scaled_dataset.reshape(1,len(X_scaled_dataset), 4)
    Y_reshape = Y_scaled_dataset.reshape(1, len(Y_scaled_dataset)).T[0]

    # load json and create model
    #with graph.as_default():
    # model = Sequential()
    # model.add(LSTM(32, input_shape=(50, 4)))
    # model.add(Dropout(0.5))
    # model.add(Dense(output_dim=1))
    # model.add(Activation('relu'))


    # model.compile(loss='mse',
    #             optimizer='rmsprop',
    #             metrics=['accuracy'])
    # model.load_weights("model.h5")
    #model = load_model('./app/model1.h5')
    X_cols = ['High', 'Low', 'Open', 'Volume']
    predictions = np.array([])
    for index, row in aapl[50:].iterrows():
        input = aapl[X_cols].iloc[index-50:index]
        scaled_input = X_scaler.fit_transform(input)
        scaled_prediction = model.predict(scaled_input.reshape(1,50,4))
        unscaled_prediction = Y_scaler.inverse_transform(scaled_prediction)
        predictions = np.append(predictions, unscaled_prediction)

    padding = np.zeros(50)
    toAdd = np.append(padding, predictions)
    data_frame = aapl
    data_frame['predicted_close'] = toAdd
    return data_frame


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

@app.route('/applestock', methods=['GET','POST'])
@login_required
@payment_required
def applestock():
    results = get_stocks()[-50:].values
    #charts = GoogleCharts(app)
    #my_chart = LineChart("my_chart", options={'title': 'My Chart'}, data_url=url_for(results.any()))
    return render_template('apple.html', results=results)


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
        db.child("users").child(data['email'].split('@')[0]).update(data)

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
            db.child("users").child(data['email'].split("@")[0]).set(data)
            flash('Thanks for registering. Please login.')
            return redirect(url_for('login'))
        except:
            error = 'Oh no! That username and/or email already exist. Please try again.'
    else:
        flash_errors(form)
    return render_template('register.html', form=form, error=error)

@app.errorhandler(500)
def internal_error(error):
    #db.session.rollback()
    return render_template('500.html'), 500

@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404