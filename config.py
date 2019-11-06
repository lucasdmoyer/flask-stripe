import os

basedir = os.path.abspath(os.path.dirname(__file__))
DATABASE = 'test.db'
SECRET_KEY = 'my precious'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test.db')

consumer_key = '4VARrokJb84kXZUDpw25JVoEY'
consumer_secret = 'ZhveyczqzKGRXHgHoiDMlrUPSbhXnkY6j1ZHXpALwcq6PzdnIL'
access_token = '369300329-trRjg6GVVTMXmjsu9VU7VMRJvIx0L6D3LxDNC5Bo'
access_token_secret ='FBlht7nQcJi5un1DGBWlhW0PzuBzfz4iReywZkp2tvbXD'

firebaseConfig = {
  "apiKey": "AIzaSyD8HxeoIasr4EnjlnR-q5EmVlYnCLzvUWw",
  "authDomain": "stock-future.firebaseapp.com",
  "databaseURL": "https://stock-future.firebaseio.com",
  "projectId": "stock-future",
  "storageBucket": "",
  "messagingSenderId": "363827879320",
  "appId": "1:363827879320:web:632794d71c6a289bc4dfed",
  "measurementId": "G-EHQQVTLTRW"
}

nytimes = 'mAgfhvE6pGRxyk4cw3M0XOsh90tOuGBD'