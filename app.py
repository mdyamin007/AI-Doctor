from flask import Flask, render_template, url_for, request, jsonify, make_response
from flask_cors import CORS, cross_origin
import pandas as pd
import numpy as np
import pickle
from pymongo import MongoClient
import json

app = Flask(__name__)

test_data = pd.read_csv('Testing.csv', sep=',')
test_data = test_data.drop('prognosis', axis=1)
symptoms = list(test_data.columns)
model = pickle.load(open('model.pkl', 'rb'))


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        user_symptoms = [request.form['symptom-1'], request.form['symptom-2'],
                         request.form['symptom-3'], request.form['symptom-4'], request.form['symptom-5']]
        y = []
        for i in range(len(symptoms)):
            y.append(0)
        for i in range(5):
            y[symptoms.index(user_symptoms[i])] = 1
        prediction = model.predict([np.array(y)])
        ans = prediction[0]
        return render_template('index.html', symptoms=symptoms, prediction="You have {}".format(ans))

    else:
        return render_template('index.html', symptoms=symptoms)


@app.route('/webhook', methods=['POST'])
@cross_origin()
def webhook():
    req = request.get_json(silent=True, force=True)
    res = ProcessRequest(req)
    res = json.dumps(res, indent=4)
    print(res)
    response = make_response(res)
    response.headers['Content-Type'] = 'application/json'
    return response


def ProcessRequest(req):
    cluster = MongoClient(
        "mongodb+srv://mdyamin:yamin787898@cluster0.5bduk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
    db = cluster['aidoctor']
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

        webhookresponse = 'Hey {}, what symptoms do you have? please enter one of your symptoms.(Ex. headeache, vomiting etc.)'.format(
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

        document = collection.find_one_and_update(
            {'name': name}, 
            { '$push': { 'symptoms': symptom}}
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
        disease = model.predict([np.array(y)])
        disease = disease[0]
             
        webhookresponse = f"Hey {name}. You may have {disease}."

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
    app.run(debug=True)
