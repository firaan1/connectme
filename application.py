import os
import hashlib
import json

from flask import Flask, session, render_template, request, flash, redirect, url_for, abort
from flask_session import Session

app = Flask(__name__)

# jinja2
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

# Set up database
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

users_dict = {"a": {"password": "0cc175b9c0f1b6a831c399e269772661", "channels_user": [], "channels_owner": []}}

channels_dict_test = {"c1": {"owner" : "a", "channel_messages" : {0 : {"user" : "a", "message" : "xx", "timestamp" : "sadfs"}}}}
channels_dict = channels_dict_test
# channels_dict = {}


@app.before_request
def before_request():
    if not users_dict:
        session['logged_in'] = False
    try:
        str(session['logged_in'])
    except:
        session['logged_in'] = False
    if not session['logged_in']:
        if request.endpoint not in ['index', 'login', 'register']:
            return redirect(url_for('index'))
    else:
        if request.endpoint in ['login', 'register']:
            return redirect(url_for('index'))

@app.route("/")
def index():
    return render_template('index.html', users_dict = users_dict, sessionid = session['logged_in'], channels_dict = channels_dict)

@app.route("/channels", methods = ["GET", "POST"])
def channels():
    return render_template('channels.html', channels_dict = json.dumps(channels_dict), users_dict = json.dumps(users_dict))

@app.route("/addchannel", methods = ["POST"])
def addchannel():
    channel_info = json.loads(request.form.get("channel_info"))
    users_dict[session['logged_in']]['channels_user'].append(list(channel_info.keys())[0])
    users_dict[session['logged_in']]['channels_owner'].append(list(channel_info.keys())[0])
    channels_dict.update(json.loads(request.form.get("channel_info")))

@app.route("/channels/<string:channel>")
def channel(channel):
    return render_template('channel.html', users_dict = users_dict, channels_dict = channels_dict)

# @app.route("/removechannel", methods = ["POST"])
# def removechannel():
#     channels_dict.pop()

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        if not users_dict:
            return render_template('error.html', message = "Unknown user")
        for user in users_dict:
            if user == username:
                if users_dict[user]['password'] == password_hash:
                    session['logged_in'] = username
                else:
                    render_template('error.html', message = "Check user credentials")
        if not session['logged_in']:
            render_template('error.html', message = "Unknown user")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout", methods = ["GET", "POST"])
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))

@app.route("/register", methods = ["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_retype = request.form.get('password_retype')
        if not password == password_retype:
            return render_template('error.html', message = "Check retyping password")
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

        # adding users
        if users_dict:
            for user in users_dict:
                if user == username:
                    return render_template('error.html', message = "User already exists")
        users_dict[username] = {
        'password' : password_hash,
        'channels_user' : [],
        'channels_owner' : []
        }
        session['logged_in'] = username
        return redirect(url_for('index'))
    return render_template('register.html')
