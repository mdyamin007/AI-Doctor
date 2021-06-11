import csv
fields = []
description = {}

with open('disease_description.csv') as csvfile:
    csvreader = csv.reader(csvfile)
    fields = next(csvreader)

    for row in csvreader:
        disease, desc = row
        description[disease] = desc
    
print(description)
