from flask import Flask, render_template, request, abort, jsonify
from bson import json_util

import uuid, json   
import subprocess
    
import pymongo
from pymongo import MongoClient
 

config = {}
execfile('etc/linky.conf', config) 

app = Flask(__name__)
 
@app.route('/')
def home():
    return render_template('landing.html')


@app.route('/api/linky/', methods=['POST'])
def api_post():

    target_url = request.form['url']
    linky_id = str(uuid.uuid4())

    if not target_url:
        abort(404)
    
    # Generate the PDF
    wkhtml_to_pdf_command = config['WKHTMLTOPDF_FS_PATH'] + ' --quiet --load-error-handling ignore -B 0 -L 0 -R 0 -T 0 ' + target_url + ' ' + config['IMAGE_DIR'] + linky_id + '.pdf'    
    subprocess.call(wkhtml_to_pdf_command, shell=True)

    # Generate the full-size image
    convert_command = config['CONVERT_PATH'] + ' -quiet ' + config['IMAGE_DIR'] + linky_id + '.pdf[0] ' + config['IMAGE_DIR'] + linky_id + '.jpg'
    subprocess.call(convert_command, shell=True)

    # Remove the PDF
    subprocess.call('rm ' + config['IMAGE_DIR'] + linky_id + '.pdf', shell=True)
    

    #exec($master_config['WKHTMLTOPDF_FS_PATH'] . ' --quiet --load-error-handling ignore -B 0 -L 0 -R 0 -T 0 ' . $url . ' ' . $thumbs_dir . $slug . '.pdf');
    #exec('convert -quiet ' . $thumbs_dir . $slug . '.pdf[0] ' . $thumbs_dir . $slug . '.jpg');
    #exec('convert -quiet ' . $thumbs_dir . $slug . '.jpg -resize 250x250 ' . $thumbs_dir . $slug . '_thumb.jpg');


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
    
    response_object = {"linky_id": linky_id, 'linky_url': '/static/img/linkys/' + linky_id + '.jpg'}
    
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

    response_object = {"linky_id": existing_linky['linky_id'], 'linky_url': '/static/img/linkys/' + existing_linky  ['linky_id'] + '.jpg'}

    response = jsonify(response_object)
    response.headers['Content-Type'] = "application/json"
    response.status_code = 200        

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)