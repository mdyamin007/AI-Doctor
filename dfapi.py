import os
from dialogflow_v2.types import TextInput, QueryInput
from dialogflow_v2 import SessionsClient
from google.api_core.exceptions import InvalidArgument


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'private_key.json'

DIALOGFLOW_PROJECT_ID = 'ai-doctor-ebfe'
DIALOGFLOW_LANGUAGE_CODE = 'en'
SESSION_ID = 'me'

text_to_be_analyzed = "Nishat 24"

session_client = SessionsClient()
session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
text_input = TextInput(text=text_to_be_analyzed, language_code=DIALOGFLOW_LANGUAGE_CODE)
query_input = QueryInput(text=text_input)
try:
    response = session_client.detect_intent(session=session, query_input=query_input)
except InvalidArgument:
    raise

print("Query text:", response.query_result.query_text)
print("Detected intent:", response.query_result.intent.display_name)
print("Detected intent confidence:", response.query_result.intent_detection_confidence)
print("Fulfillment text:", response.query_result.fulfillment_text)
print("\n\n\n")

ret = {}
intent = response.query_result.intent.display_name

if intent == 'get_info':
    ret = {
        'Reply' : response.query_result.fulfillment_messages[0].text.text[0]
    }
    
else :
    ret = {
    'Reply' : response.query_result.fulfillment_text
    }

print(ret)