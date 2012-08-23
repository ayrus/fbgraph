from django.shortcuts import render_to_response, redirect, HttpResponseRedirect
from django.template import RequestContext
from django.conf import settings
from datetime import datetime
from hashlib import md5
from pytz import timezone

import oauth2 as oauth
import simplejson as json
import urllib, urlparse
import os

def home(request):
    return render_to_response('index.html', locals(),
                                          context_instance=RequestContext(request))

def connect(request):
    
    #detect if user already has an auth token (in the valid timeframe).
    
    return HttpResponseRedirect(settings.FB_REQUEST_TOKEN_URL + '?client_id=%s&redirect_uri=%s&scope=%s' 
                                        % (settings.FB_APPID,  urllib.quote_plus(settings.FB_CALLBACK), settings.FB_PERMISSIONS))	

def callback(request):
    
    
    consumer = oauth.Consumer(key=settings.FB_APPID, \
                              secret=settings.FB_APPSECRET)
    
    client = oauth.Client(consumer)
    
    request_url = settings.FB_ACCESS_TOKEN_URL + '?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (settings.FB_APPID, settings.FB_CALLBACK, settings.FB_APPSECRET, request.GET.get('code')) 
    
    response, content = client.request(request_url, 'GET')
    
    access_token = dict(urlparse.parse_qsl(content))['access_token']
    
    if response.status is 200:
    
    	request.session['fb_access_token'] = access_token
	
	endpoint = settings.FB_RETRIEVE_ID_URL + '?access_token=%s' % access_token
	
	response, content = client.request(endpoint)
	
	if response.status is 200:
	    
	    content = json.loads(content)
	    
	    request.session['id'] = content['id']
	    
	    return redirect('/process')
    else:
	#do-smth
	pass
    
def process(request):
    
    if hasattr(request, 'session') and hasattr(request.session, \
                                               'session_key') and \
       getattr(request.session, 'session_key') is None:
      
        request.session.create()
    
    # Generate a unique request ID hash from the session key for this particular
    # request.
    requestID = md5(request.session.session_key +
            str(datetime.now())).hexdigest() 
    
    
    consumer = oauth.Consumer(key=settings.FB_APPID, \
                              secret=settings.FB_APPSECRET)
    
    client = oauth.Client(consumer)
    
    #CHANGE SPECIFIC SETTINGS HERE.
    
    endpoint = settings.FB_RETRIEVE_ID_URL + '/posts?since=1325376000&limit=100&fields=created_time&access_token=%s' % request.session['fb_access_token']
	    
    response, content = client.request(endpoint)
    
    content = json.loads(content)
    
    file_data = ""
    
    #ADD GRAPH.
    
    post_frequency = {0 : 0, 1 : 0, 2 : 0, 3 : 0, 4 : 0, 5 : 0, 6 : 0}
    
    time_matrix = [[0 for hour in range(24)] for day in range(7)]
    
    for data in content['data']:
	
	date = datetime.strptime(data['created_time'][:-5], "%Y-%m-%dT%H:%M:%S") 
	
	#CHANGE THE CONVERSION.
	
	locale = date.replace(tzinfo=timezone('UTC')).astimezone(timezone('Asia/Kolkata'))
	
	day = locale.weekday()
	
	hour = int(locale.strftime("%H"))

	time_matrix[day][hour] = time_matrix[day][hour] + 1	
	
	post_frequency[day] = post_frequency[day] + 1
	
    day_frequency = post_frequency.values()
    
    return render_to_response('result.html', locals(),
	                                      context_instance=RequestContext(request))