from flask import Flask, render_template, url_for, request
import pandas as pd
import numpy as np
import pickle

app = Flask(__name__)

test_data = pd.read_csv('Testing.csv', sep=',')
test_data = test_data.drop('prognosis', axis=1)
symptoms = list(test_data.columns)
model = pickle.load(open('model.pkl', 'rb'))

@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        user_symptoms = [request.form['symptom-1'], request.form['symptom-2'], request.form['symptom-3'], request.form['symptom-4'], request.form['symptom-5']]
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

if __name__ == '__main__':
    app.run(debug=True)