from django.shortcuts import render_to_response, redirect, HttpResponseRedirect
from django.template import RequestContext
from django.conf import settings
from fbgraph.app.forms import requestForm
from datetime import datetime
from hashlib import md5
from pytz import timezone
from time import mktime

import oauth2 as oauth
import simplejson as json
import urllib, urlparse
import os

def home(request):
    
    FB_LIKE_LINK = settings.FB_LIKE_LINK
    
    if request.method == "POST":
    
    	form = requestForm(request.POST) 
	
	if form.is_valid():
	    
	    request.session['fbgraph_limit'] = request.POST['limit']
	    
	    request.session['fbgraph_timezone'] = request.POST['timezone']
	    
	    from_date = datetime.strptime(request.POST['from_date'], "%d-%m-%Y")
	    
	    from_date = int(mktime(from_date.timetuple()))
	    
	    request.session['fbgraph_from_date'] = from_date
	    
	    request.session['fbgraph_from_date_plain'] = request.POST['from_date']
	    
	    request.session['fbgraph_to_date'] = request.POST['to_date']
	    
	    return HttpResponseRedirect(settings.FB_REQUEST_TOKEN_URL + '?client_id=%s&redirect_uri=%s&scope=%s'
			                            % (settings.FB_APPID, urllib.quote_plus(settings.FB_CALLBACK), settings.FB_PERMISSIONS)) 	    
	
    else:
	
	form = requestForm()
    
    return render_to_response('index.html', locals(),
                                          context_instance=RequestContext(request))	

def callback(request):
    
    
    #consumer = oauth.Consumer(key=settings.FB_APPID, \
                              #secret=settings.FB_APPSECRET)
    
    #client = oauth.Client(consumer)
    
    #request_url = settings.FB_ACCESS_TOKEN_URL + '?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (settings.FB_APPID, settings.FB_CALLBACK, settings.FB_APPSECRET, request.GET.get('code')) 
    
    #response, content = client.request(request_url, 'GET')
    
    #access_token = dict(urlparse.parse_qsl(content))['access_token']
    
    #if response.status is 200:
    
    	#request.session['fb_access_token'] = access_token
	
	#endpoint = settings.FB_RETRIEVE_ID_URL + '?access_token=%s' % access_token
	
	#response, content = client.request(endpoint)
	
	#if response.status is 200:
	    
	    #content = json.loads(content)
	    
	    #request.session['id'] = content['id']
	    
    return redirect('/process')
    #else:
	##do-smth
	#pass
    
def _retrieveContent(request, endpoint, client):
    
    print endpoint
	    
    response, content = client.request(endpoint)    
        
    content = json.loads(content)
    
    try:
	endpoint = content['paging']['next']
    except KeyError:
	endpoint = None
    
    return content, endpoint
    
def process(request):
    
    post_frequency = {0 : 0, 1 : 0, 2 : 0, 3 : 0, 4 : 0, 5 : 0, 6 : 0}
    
    to_date = request.session['fbgraph_to_date']
    
    from_date = request.session['fbgraph_from_date_plain']
    
    date_threshold = datetime.strptime(to_date, "%d-%m-%Y")
    
    time_matrix = [[0 for hour in range(24)] for day in range(7)]
    
    records = 0
    
    records_threshold = int(request.session["fbgraph_limit"])
    
    flag = True
    
    consumer = oauth.Consumer(key=settings.FB_APPID, \
                              secret=settings.FB_APPSECRET)
    
    client = oauth.Client(consumer)    
    
    endpoint = settings.FB_RETRIEVE_ID_URL + '/posts?until=%s&limit=1000&fields=created_time&access_token=%s' % (request.session['fbgraph_from_date'], request.session['fb_access_token'])
    
    while flag:
	
	content, endpoint = _retrieveContent(request, endpoint, client)
    
	for data in content['data']:
	    
	    date = datetime.strptime(data['created_time'][:-5], "%Y-%m-%dT%H:%M:%S") 
	    
	    if date < date_threshold:
		
		flag = False
		break
	    
	    locale = date.replace(tzinfo=timezone('UTC')).astimezone(timezone(request.session['fbgraph_timezone']))
	    
	    day = locale.weekday()
	    
	    hour = int(locale.strftime("%H"))
    
	    time_matrix[day][hour] = time_matrix[day][hour] + 1	
	    
	    records = records + 1
	    
	    post_frequency[day] = post_frequency[day] + 1
	
	if records >= records_threshold:
	 
	    flag = False
	    
    day_frequency = [ (val / float(records)) for val in post_frequency.values()]
    
    return render_to_response('result.html', locals(),
	                                      context_instance=RequestContext(request))