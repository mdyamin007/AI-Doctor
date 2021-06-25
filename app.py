from flask import Flask, render_template, request, redirect, url_for, session, make_response
from flask_cors import cross_origin, CORS
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime
from dbchat import save_message, get_messages
from pickle import load
from pandas import read_csv
from numpy import array
from csv import reader
from json import dumps
from dialogflow_v2.types import TextInput, QueryInput
from dialogflow_v2 import SessionsClient
from google.api_core.exceptions import InvalidArgument
from os import environ

app = Flask(__name__)
app.secret_key = '09cd6cb8206a12b54a7ddb28566be757'
socketio = SocketIO(app, cors_allowed_origins="*")
bcrypt = Bcrypt(app)

cluster = MongoClient(
        "mongodb+srv://mdyamin:yamin787898@cluster0.5bduk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = cluster['aidoctor']

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/bot')
@cross_origin()
def chat_bot():
    if "email" in session:
        return render_template('bot.html')
    else:
        return redirect(url_for('login', next='/bot'))

@app.route('/dashboard')
@cross_origin()
def dashboard():
    if "email" in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/profile')
@cross_origin()
def profile():
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@cross_origin()
def settings():
    if request.method == "GET":
        return render_template('settings.html')
    else:
        collection = db['users']
        form_data = request.form
        query_data = {
            "email": form_data['email']
        }
        result = collection.find_one(query_data)
        response = ''
        if bcrypt.check_password_hash(result['password'], form_data['current_password']) == True:
            update_data = {
                "name": form_data['name'],
                "password": bcrypt.generate_password_hash(form_data['new_password1']).decode('utf-8'),
                "userType": form_data['userType']
            }
            result = collection.find_one_and_update(query_data, { "$set" : update_data })
            if result:
                response = 'succeeded'
                session['name'] = form_data['name']
                session['userType'] = form_data['userType']
        else:
            response = 'failed'
        return render_template('settings.html', response=response)

@app.route('/contact')
@cross_origin()
def contact_us():
    return render_template('contactUs.html')

@app.route('/services')
@cross_origin()
def services():
    return render_template('services.html')

@app.route('/signup', methods=['POST'])
@cross_origin()
def sign_up():
    collection = db['users']
    form_data = request.form
    pw_hash =  bcrypt.generate_password_hash(form_data['password']).decode('utf-8')
    result = collection.find_one({'email': form_data['email']})
    if result == None:
        id = collection.insert_one({
            'name': form_data['name'],
            'email': form_data['email'],
            'password': pw_hash,
            'userType': form_data['userType']
        }).inserted_id
        response = ''
        if id == '':
            response = 'failed'
        else:
            response = 'success'
    else:
        response = 'failed'
    return render_template('signup.html', response=response)


@app.route('/login', methods=['GET', 'POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        collection = db['users']
        form_data = request.form
        next_url = request.form.get('next')
        query_data = {
            "email": form_data['email']
        }
        result = collection.find_one(query_data)
        response = ''
        if result == None:
            response = 'failed'
        else:
            pw = form_data['password']
            if bcrypt.check_password_hash(result['password'], pw) == True:
                response = 'succeeded'
                session['email'] = form_data['email']
                session['name'] = result['name']
                session['userType'] = result['userType']
            else:
                response = 'failed'
        
        if response == 'failed':
            return render_template('login.html', response=response)
        else:
            if next_url:
                return redirect(next_url)
            else:
                return redirect(url_for('dashboard'))
    else:
        if "email" in session:
            return redirect(url_for("dashboard"))
        else:
            return render_template('login.html')

@app.route('/logout')
@cross_origin()
def logout():
    if 'email' in session:
        session.pop("email", None)
        session.pop("username", None)
        session.pop("userType", None)
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/resetdb')
@cross_origin()
def reset_database():
    collection1 = db['user_symptomps']
    collection2 = db['users']
    collection3 = db['messages']
    collection1.delete_many({})
    collection2.delete_many({})
    collection3.delete_many({})
    return "Database Cleared"

@app.route('/chat')
@cross_origin()
def chat():
    if "email" in session:
        messages = get_messages()
        return render_template('chat.html', username=session['name'], userType=session['userType'], messages=messages)
    else:
        return redirect(url_for('login', next='/chat'))


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room: {}".format(data['username'], data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    save_message(data['message'], data['username'], data['userType'])
    socketio.emit('receive_message', data)


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room".format(data['username']))
    join_room(1)
    text = data['username'] + "(" + data['userType'] + ")" + " has joined the room"
    save_message(text, data['username'], data['userType'])
    socketio.emit('join_room_announcement', data)


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room".format(data['username']))
    leave_room(1)
    text = data['username'] + "(" + data['userType'] + ")" + " has left the room"
    save_message(text, data['username'], data['userType'])
    socketio.emit('leave_room_announcement', data)



test_data = read_csv('ml/Testing.csv', sep=',')
test_data = test_data.drop('prognosis', axis=1)
symptoms = list(test_data.columns)
model = load(open('ml/model.pkl', 'rb'))
db = cluster['aidoctor']


fields = []
description = {}
precautionDictionary = {}

with open('ml/disease_description.csv') as csvfile:
    csvreader = reader(csvfile)
    fields = next(csvreader)

    for row in csvreader:
        disease, desc = row
        description[disease] = desc

with open('ml/symptom_precaution.csv') as csv_file:

        csv_reader = reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _prec={row[0]:[row[1],row[2],row[3],row[4]]}
            precautionDictionary.update(_prec)


@app.route('/webhook', methods=['POST'])
@cross_origin()
def webhook():
    req = request.get_json(silent=True, force=True)
    res = ProcessRequest(req)
    res = dumps(res, indent=4)
    print(res)
    response = make_response(res)
    response.headers['Content-Type'] = 'application/json'
    return response


def ProcessRequest(req):
    collection = db['user_symptoms']
    result = req.get('queryResult')
    intent = result.get('intent').get('displayName')

    if intent == 'get_info':
        name = result.get('parameters').get('any')
        age = result.get('parameters').get('number')
        collection.insert_one({
            'name': name,
            'age': age,
            'symptoms': []
        })

        webhookresponse = 'Hey {}, what symptoms do you have? please enter one of your symptoms.(Ex. headache, vomiting etc.)'.format(
            name)

        return {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [
                            webhookresponse
                        ]

                    }
                }
            ]
        }

    elif intent == 'get_symptom':
        name = result.get('outputContexts', [])[0].get('parameters').get('any')
        symptom = result.get('parameters').get('symptom')

        collection.find_one_and_update(
            {'name': name},
            {'$push': {'symptoms': symptom}}
        )

        webhookresponse = "Enter one more symptom beside {}. (Enter 'No' if not)".format(
            symptom)

        return {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [
                            webhookresponse
                        ]
                    }
                }
            ]
        }
    elif intent == 'get_symptom - no':
        name = result.get('outputContexts', [])[1].get('parameters').get('any')
        user_symptoms = collection.find_one({'name': name})
        user_symptoms = list(user_symptoms.get('symptoms'))
        y = []
        for i in range(len(symptoms)):
            y.append(0)
        for i in range(len(user_symptoms)):
            y[symptoms.index(user_symptoms[i])] = 1
        disease = model.predict([array(y)])
        disease = disease[0]

        precaution_list = precautionDictionary[disease]

        webhookresponse = f"""Hey {name}. You might have {disease}.

        {description[disease]}

        Take following precautions: 

        """
        i = 1
        for precaution in precaution_list:
            if precaution == "":
                continue
            webhookresponse = webhookresponse + str(i) + ". " + precaution + ", "
            i = i + 1
        
        if "email" in session:
            user_collection = db['users']
            query_data = {
                "email": session['email']
            }
            result = user_collection.find_one_and_update(query_data, {
                "$set" : {"symptoms": user_symptoms, "disease": disease}
            })

        return {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [
                            webhookresponse
                        ]
                    }
                }
            ]
        }




if __name__ == '__main__':
    socketio.run(app, debug=True)
