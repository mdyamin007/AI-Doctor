import csv
import json

fields = []

with open('Testing.csv', 'r') as f:
    reader = csv.reader(f)
    fields = next(reader)

json_object = json.dumps(fields, indent=4)

with open('suggestions.json', 'w') as f:
    f.write(json_object)