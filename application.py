import os
import hashlib
import json
from datetime import datetime

from flask import Flask, session, render_template, request, flash, redirect, url_for, abort
from flask_session import Session
from flask_socketio import SocketIO, emit

from functools import wraps

app = Flask(__name__)

# jinja2
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

Session(app)

users_dict = {}

channels_dict = {}

max_posts = 100

# users_dict.update({"a": {"password": "0cc175b9c0f1b6a831c399e269772661", "channels_user": [], "channels_owner": []}, 'b': {'password': '92eb5ffee6ae2fec3ad71c777531578f', 'channels_user': [], 'channels_owner': []}})
# users_dict.update({"a": {"password": "0cc175b9c0f1b6a831c399e269772661", "channels_user": ["c1"], "channels_owner": ["c1"]}, 'b': {'password': '92eb5ffee6ae2fec3ad71c777531578f', 'channels_user': ["c1"], 'channels_owner': []}})
# channels_dict.update({"c1": {"owner" : "a", "channel_messages" : {0 : {"user" : "a", "message" : "xx", "date" : "date", "time" : "time", "index" : 0}}}})

# taken from flask webpage decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] is None or not session['logged_in']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] :
            return render_template('error.html', message = "User already logged in!")
        return f(*args, **kwargs)
    return decorated_function

@app.before_first_request
def before_first_request():
    try:
        if users_dict and session['logged_in']:
            if session['logged_in'] not in list(users_dict.keys()):
                session['logged_in'] = False
                session['logged_pass'] = False
    except:
        session['logged_in'] = False
        session['logged_pass'] = False

@app.before_request
def before_request():
    try:
        if users_dict and session['logged_in']:
            if session['logged_in'] not in list(users_dict.keys()):
                session['logged_in'] = False
                session['logged_pass'] = False
    except:
        session['logged_in'] = False
        session['logged_pass'] = False

# @app.before_request
# def before_request():
#     if not users_dict:
#         session['logged_in'] = False
#         session['logged_pass'] = False
#     try:
#         str(session['logged_in'])
#         if session['logged_in'] == "False":
#             session['logged_in'] = False
#             session['logged_pass'] = False
#     except:
#         session['logged_in'] = False
#         session['logged_pass'] = False
#     if not session['logged_in']:
#         if request.endpoint not in ['index', 'login', 'register', 'error']:
#             return redirect(url_for('index'))
#     else:
#         if request.endpoint in ['login', 'register']:
#             return redirect(url_for('index'))

@app.route("/")
def index():
    try:
        session['logged_in']
    except:
        session['logged_in'] = False
    return render_template('index.html', users_dict = json.dumps(users_dict), sessionid = session['logged_in'], channels_dict = channels_dict)

@app.route("/channels", methods = ["GET", "POST"])
@login_required
def channels():
    return render_template('channels.html', channels_dict = json.dumps(channels_dict), user_dict = json.dumps(users_dict[session['logged_in']]))

@app.route("/addchannel", methods = ["POST"])
@login_required
def addchannel():
    channel_info = json.loads(request.form.get("channel_info"))
    users_dict[session['logged_in']]['channels_user'].append(list(channel_info.keys())[0])
    users_dict[session['logged_in']]['channels_owner'].append(list(channel_info.keys())[0])
    channels_dict.update(json.loads(request.form.get("channel_info")))
    return redirect(url_for('channels'))

@socketio.on("submit post")
def post(data):
    post_text = data['post_text']
    channel = data['channel']
    posts = channels_dict[channel]['channel_messages']
    if not posts:
        index = 0
    else:
        indexes = sorted(list(posts.keys()))
        index = indexes[-1] + 1
        index_rm = indexes[0]
        if len(posts) == max_posts:
            posts.pop(index_rm)
    post_dict = {
    index : {
        'user' : session['logged_in'],
        'message' : post_text,
        'date' : datetime.now().strftime("%Y-%m-%d"),
        'time' : datetime.now().strftime("%H:%M:%S"),
        'index' : index
        }
    }
    posts.update(post_dict)
    emit("post list", json.dumps(post_dict), broadcast=True)

@socketio.on("delete post")
def delpost(data):
    post_index = int(data['post_index'])
    channel = data['channel']
    channels_dict[channel]['channel_messages'].pop(post_index)
    current_post = json.dumps({'channel' : channel, 'post_index' : post_index})
    emit("post delete", current_post, broadcast=True)

@app.route("/modchannel", methods = ["POST"])
@login_required
def modchannel():
    channel = request.form.get('current_channel')
    button = request.form.get('button')
    if button == 'delete':
        channels_dict.pop(channel)
        users_dict[session['logged_in']]['channels_user'].remove(channel)
        users_dict[session['logged_in']]['channels_owner'].remove(channel)
    elif button == 'leave':
        users_dict[session['logged_in']]['channels_user'].remove(channel)
    elif button == 'join':
        users_dict[session['logged_in']]['channels_user'].append(channel)
    return redirect(url_for('channels'))

@app.route("/channels/<string:channel>")
@login_required
def channel(channel):
    if channel not in channels_dict:
        return render_template('error.html', message = "Unknown channel")
    if channel not in users_dict[session['logged_in']]['channels_user']:
        return render_template('error.html', message = "Join the channel to access it")
    channel_posts = channels_dict[channel]['channel_messages']
    return render_template('channel.html', channels_dict = json.dumps(channels_dict), channel = channel, max_posts = max_posts)

@app.route("/login", methods = ["GET", "POST"])
@logout_required
def login():
    if request.method == "POST":
        session_logged_in = request.form.get('session_logged_in')
        username = request.form.get('username')
        password = request.form.get('password')
        if session_logged_in:
            session_logged_in = json.loads(session_logged_in)
            username = session_logged_in['user']
            password_hash = session_logged_in['password']
        else:
            password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        if not users_dict:
            return render_template('error.html', message = "Unknown user")
        for user in users_dict:
            if user == username:
                if users_dict[user]['password'] == password_hash:
                    session['logged_in'] = username
                    session['logged_pass'] = password_hash
                else:
                    return render_template('error.html', message = "Check user credentials")
        if not session['logged_in']:
            return render_template('error.html', message = "Unknown user")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout", methods = ["GET", "POST"])
@login_required
def logout():
    session['logged_in'] = False
    session['logged_pass'] = False
    return redirect(url_for('index'))

@app.route("/register", methods = ["GET", "POST"])
@logout_required
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
        session['logged_pass'] = password_hash
        return redirect(url_for('index'))
    return render_template('register.html')
