import db 
import json 

client = db.Connect.get_connection()

# select the database and the collection
db = client['salt_pr_code_changes']
collection = db['code_changes']

# empty set to store the processed locations
locations_set = set()

# iterate over all documents in the collection
for document in collection.find():
    # fetch the location
    location = document['location']
    # split the string at '@' and select the first part
    trimmed_location = location.split('@')[0]
    # # split the string at '.' and exclude the last part
    # trimmed_location = '.'.join(trimmed_location.split('.')[:-1])
    # add to set
    locations_set.add(trimmed_location)

# convert set to list
locations_list = list(locations_set)

# dump to JSON string with indentation
json_str = json.dumps(locations_list, indent=4)

# write the JSON string to a file
with open('pr_changed_modules.json', 'w') as f:
    f.write(json_str)

