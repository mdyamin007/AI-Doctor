import pandas as pd 
from sklearn.svm import SVC
import pickle

train_data = pd.read_csv('Training.csv', sep=',')
test_data = pd.read_csv('Testing.csv', sep=',')

train_data = train_data.drop('Unnamed: 133', axis=1)

X_train = train_data.drop('prognosis',axis=1)
y_train = train_data['prognosis'].copy()
X_test = test_data.drop('prognosis', axis=1)
y_test = test_data['prognosis'].copy()


model = SVC()

model.fit(X_train, y_train)

pickle.dump(model, open('model.pkl', 'wb'))



