from pymongo import MongoClient, DESCENDING
from datetime import datetime

cluster = MongoClient(
        "mongodb+srv://mdyamin:yamin787898@cluster0.5bduk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = cluster['aidoctor']

messages_collection = db.get_collection('messages')

def save_message(text, sender):
    messages_collection.insert_one({
        'text':text,
        'sender':sender,
        'created_at':datetime.now()
        })
    
def get_messages():
    messages = list(messages_collection.find({}).sort('_id', DESCENDING))
    for message in messages:
        message['created_at'] = message['created_at'].strftime("%d %b, %H:%M")
    return messages[::-1]