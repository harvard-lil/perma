from flask import Flask, render_template, request, abort, jsonify
from bson import json_util

import smtplib

from email.mime.text import MIMEText

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

    target_url = request.form['url']
	
    if not target_url:
        abort(404)
        
    if target_url[0:4] != 'http':
        target_url = 'http://' + target_url
        
    # Setup mongo connection
    client = MongoClient(config['MONGO_HOST'], config['MONGO_PORT'])
    linky_db = client.linky
    links_collection = linky_db.links
    links_collection.ensure_index([('linky_number', pymongo.DESCENDING)])
        
    # We'll generate our hash from this count.
    # Externally, the linky id is the hash, internally, it's a just an incremented int
    linky_number = links_collection.count()

    # Playing around with short url hashes
    hashids_lib = hashids(config['SALT'])
    linky_hash = hashids_lib.encrypt(linky_number)
    
    image_generation_command = config['LINKY_HOME'] + '/lib/phantomjs ' + config['LINKY_HOME'] + '/lib/rasterize.js "' + target_url + '" ' + config['LINKY_HOME'] + '/static/img/linkys/' + str(linky_number) + '.png'
    subprocess.call(image_generation_command, shell=True)

    new_linky = {"url": target_url, "linky_number": linky_number}
    links_collection.insert(new_linky)
        
    # if we want to do some file uploading
    #f = request.files['the_file']
    #f.save('/var/www/uploads/uploaded_file.txt')
    
    response_object = {"linky_id": linky_hash, 'linky_url': config['WEB_BASE'] + '/static/img/linkys/' + str(linky_number) + '.png'}
    
    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 201
    
    return response
 
 
@app.route('/api/linky/<linky_id>/', methods=['GET'])
def api_get(linky_id):
    client = MongoClient(config['MONGO_HOST'], config['MONGO_PORT'])
    linky_db = client.linky
    links_collection = linky_db.links

    # Playing around with short url hashes
    hashids_lib = hashids(config['SALT'])
    
    # decode hash using:
    decrypted_ids = hashids_lib.decrypt(linky_id)
    linky_number = decrypted_ids[0]

    existing_linky = linky_db.links.find_one({"linky_number": linky_number})

    if not existing_linky:
        abort(404)

    response_object = {"linky_id": linky_id, 'linky_url': config['WEB_BASE'] + '/static/img/linkys/' + str(linky_number) + '.png'}

    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 200        

    return response
    

@app.route('/service/email-confirm/', methods=['POST'])
def service_email_confirm():
    email_address = request.form['email_address']
    linky_link = request.form['linky_link']
    
    if not email_address:
        abort(400)
    
    # TODO: we should obviously only send messages that we send.
    # lock this down.
    
    from_address = "lil@law.harvard.edu"
    to_address = email_address
    content = linky_link

    msg = MIMEText(content)
    msg['Subject'] = "The Linky link you requested"
    msg['From'] = from_address
    msg['To'] = to_address

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('localhost')
    s.sendmail(from_address, [to_address], msg.as_string())
    s.quit()

    response_object = {"sent": True}

    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 200        

    return response


@app.route('/<linky_id>/')
def linky_display(linky_id):
    
    client = MongoClient(config['MONGO_HOST'], config['MONGO_PORT'])
    linky_db = client.linky
    links_collection = linky_db.links

    # Playing around with short url hashes
    hashids_lib = hashids(config['SALT'])
    
    # decode hash using:
    decrypted_ids = hashids_lib.decrypt(str(linky_id))
    linky_number = decrypted_ids[0]

    existing_linky = linky_db.links.find_one({"linky_number": linky_number})

    if not existing_linky:
        abort(404)
    
    created_datestamp = existing_linky['_id'].generation_time
    pretty_date = created_datestamp.strftime("%B %d, %Y %I:%M GMT")
    
    return render_template('detail.html', web_base=config['WEB_BASE'], asset_number=linky_number, pretty_date=pretty_date, indexed_url=existing_linky['url'])

if __name__ == '__main__':
    app.run(host=config['FLASK_HOST'], port=config['FLASK_PORT'], debug=config['FLASK_DEBUG'])
