from django.shortcuts import render_to_response, HttpResponse


def linky_post(request):
    """ When we receive a Linky POST """
    target_url = request.POST.get('url')

    if not target_url:
        return HttpResponse(status=400)
        
    if target_url[0:4] != 'http':
        target_url = 'http://' + target_url
        
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