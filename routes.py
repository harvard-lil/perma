from flask import Flask, render_template, request, abort, jsonify
from bson import json_util

import uuid, json   
import subprocess
    
import pymongo
from pymongo import MongoClient

from lib.hashids import hashids
 

config = {}
execfile('etc/linky.conf', config) 

app = Flask(__name__)
 
@app.route('/')
def home():
    return render_template('landing.html', web_base=config['WEB_BASE'])

@app.route('/api/linky/', methods=['POST'])
def api_post():

    # Playing around with short url hashes
    hashids_lib = hashids("this is my salt")
    hash = hashids_lib.encrypt(1, 2, 3)
    numbers = hashids_lib.decrypt(hash)

    print(hash)
    print(numbers)




    target_url = request.form['url']
    linky_id = str(uuid.uuid4())

    if not target_url:
        abort(404)
    
    image_generation_command = config['LINKY_HOME'] + '/lib/phantomjs ' + config['LINKY_HOME'] + '/lib/rasterize.js "' + target_url + '" ' + config['LINKY_HOME'] + '/static/img/linkys/' + linky_id + '.png'
    subprocess.call(image_generation_command, shell=True)

    # If we were able to get the image to disk, let's add the entry our datastore
    client = MongoClient(config['MONGO_HOST'], config['MONGO_PORT'])
    linky_db = client.linky
    links_collection = linky_db.links
    links_collection.ensure_index([('linky_id', pymongo.DESCENDING)])

    new_linky = {"url": request.form['url'], "linky_id": linky_id}
    links_collection.insert(new_linky)
        
    # if we want to do some file uploading
    #f = request.files['the_file']
    #f.save('/var/www/uploads/uploaded_file.txt')
    
    response_object = {"linky_id": linky_id, 'linky_url': '/static/img/linkys/' + linky_id + '.png'}
    
    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 201
    
    return response
 
 
@app.route('/api/linky/<linky_id>', methods=['GET'])
def api_get(linky_id):
    client = MongoClient(config['MONGO_HOST'], config['MONGO_PORT'])
    linky_db = client.linky
    links_collection = linky_db.links

    existing_linky = linky_db.links.find_one({"linky_id": linky_id})

    if not existing_linky:
        abort(404)

    response_object = {"linky_id": existing_linky['linky_id'], 'linky_url': '/static/img/linkys/' + existing_linky['linky_id'] + '.png'}

    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 200        

    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
