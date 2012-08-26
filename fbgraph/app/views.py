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
    '''
    Display a view for the index page with the constructed main request form. 
    If the form has been posted to the view, parse and store the request 
    parameters in the session dict and redirect user to Facebook for auth.
    
    Keyword arguments:
    request -- the request object.
    
    Return:
    Index view on direct request or redirect to Facebook's oAuth end if a POST
    request.
    '''
    
    FB_APP_ID = settings.FB_APPID
    FB_LIKE_LINK = settings.FB_LIKE_LINK
    
    if request.method == "POST":
    
    	form = requestForm(request.POST) 
	
	if form.is_valid():
	    
	    request.session['fbgraph_limit'] = request.POST['limit']
	    
	    request.session['fbgraph_timezone'] = request.POST['timezone']
	    
	    from_date = datetime.strptime(request.POST['from_date'], "%d-%m-%Y")
	    
	    # 'Plain' is used on the graph view.
	    request.session['fbgraph_from_date_plain'] = from_date.strftime("%B, %d, %Y")
	    
	    # Convert to a UNIX timestamp (Facebook API requirement).
	    from_date = int(mktime(from_date.timetuple()))
	    
	    request.session['fbgraph_from_date'] = from_date
	    
	    request.session['fbgraph_to_date'] = request.POST['to_date']
	    
	    return HttpResponseRedirect(settings.FB_REQUEST_TOKEN_URL + '?client_id=%s&redirect_uri=%s&scope=%s'
			                            % (settings.FB_APPID, urllib.quote_plus(settings.FB_CALLBACK), settings.FB_PERMISSIONS)) 	    
	
    else:
	
	form = requestForm()
	
    # Check if any error messages have sent to print on the view.
    if "e" in request.GET:
	error = True
	errorMsg = request.GET["e"]
    
    return render_to_response('index.html', locals(),
                                          context_instance=RequestContext(request))	

def callback(request):
    '''
    Recieve a post-login callback from Facebook, try retrieving an access token
    for oAuth transactions to-from Facebook. If the user does not authorize at
    any step redirect back to index with an error.
    
    Keyword arguments:
    request -- the request object.
    
    Return:
    Redirect to view 'process' if every authoriztion goes across, or back to
    index view with an error message.
    '''
    
    FB_APP_ID = settings.FB_APPID
    FB_LIKE_LINK = settings.FB_LIKE_LINK    
    
    # Sanity check - If the user tries reaching the callback endpoint directly.
    if "code" not in request.GET and "error" not in request.GET:
	return redirect('index')
    
    # User did not add the app. Add an error message and redirect.
    if "error" in request.GET:
	response = redirect('index')
	response['Location'] += "?e=1"
	return response
    
    consumer = oauth.Consumer(key=settings.FB_APPID, \
                              secret=settings.FB_APPSECRET)
    
    client = oauth.Client(consumer)   
    
    request_url = settings.FB_ACCESS_TOKEN_URL + '?client_id=%s&redirect_uri=%s&client_secret=%s&code=%s' % (settings.FB_APPID, settings.FB_CALLBACK, settings.FB_APPSECRET, request.GET.get('code')) 
	
    response, content = client.request(request_url, 'GET')
    
    # Try obtainting the access token.
    if response.status is 200:
	
	access_token = dict(urlparse.parse_qsl(content))['access_token']
	request.session['fb_access_token'] = access_token
    
    else:
	# Couldnt't retrive the access token.
	response = redirect('index')
	response['Location'] += "?e=3"
	return response
    
    # Check if 'read_stream' permission has been granted.
    endpoint = settings.FB_RETRIEVE_ID_URL + "/permissions?access_token=%s" % access_token
    
    content, endpoint = _retrieveContent(endpoint, client)
    
    try:
	if content['data'][0]['read_stream'] == 1:
	    # Everything's good to go.
	    return redirect('process')
	    
	
    except KeyError:
	# No 'read_stream' persmission.
	response = redirect('index')
	response['Location'] += "?e=2"
	return response
    
def _retrieveContent(endpoint, client):
    '''
    Retrieve content from an oAuth endpoint through a client object and return
    the JSON parsed content.
    
    Keyword arguments:
    endpoint -- An oAuth endpoint to access.
    client -- python-oauth client object.
    
    Return:
    content -- JSON parsed output from the endpoint.
    endpoint -- Facebook specific paging 'next' URL (if exists).
    '''
	    
    response, content = client.request(endpoint)    
        
    content = json.loads(content)
    
    # See if there's more data.
    try:
	endpoint = content['paging']['next']
    except KeyError:
	endpoint = None
    
    return content, endpoint
    
def process(request):
    '''
    Retrieve user activities for the specified time-range and threshold from
    Facebook. Construct and return the array/matrix to the view to plot a graph.
    
    Keyword arumgnets:
    request -- the request object.
    
    Return:
    Rendered graph view if everything went well, else redirect with an error.
    '''
    
    FB_APP_ID = settings.FB_APPID
    FB_LIKE_LINK = settings.FB_LIKE_LINK    
    
    # Sanity check -- a user might try accessing this endpoint directly after
    # they've revoked access to the application from Facebook (internally).
    if "fbgraph_to_date" not in request.session or "fb_access_token" not in request.session:
	
	return redirect('index')
    
    # A dict to store the number of posts made each day of week. Keys are 
    # 0-indexed days of the week (i.e.: 0 - Monday; 6-Sunday). Values are the
    # respective frequencies.
    post_frequency = {0 : 0, 1 : 0, 2 : 0, 3 : 0, 4 : 0, 5 : 0, 6 : 0}
    
    from_date_plain = request.session['fbgraph_from_date_plain']
    
    to_date = request.session['fbgraph_to_date']
    
    # Date to stop looking after.
    date_threshold = datetime.strptime(to_date, "%d-%m-%Y")
    
    to_date_plain = date_threshold.strftime("%B, %d, %Y")
    
    # A 7 * 24 hour matrix corresponding the number of posts made. Each entry
    # in this matrix converts to the total number of posts made in a day x and
    # in hour y (of day x) [x - day of week][y - 24 hour in a day].
    time_matrix = [[0 for hour in range(24)] for day in range(7)]
    
    # Total number of records retrieved.
    records = 0
    
    records_threshold = int(request.session["fbgraph_limit"])
    
    # Flag - to continue/stop retrieving data.
    flag = True
    
    consumer = oauth.Consumer(key=settings.FB_APPID, \
                              secret=settings.FB_APPSECRET)
    
    client = oauth.Client(consumer)    
    
    endpoint = settings.FB_RETRIEVE_ID_URL + '/posts?until=%s&limit=1000&fields=created_time&access_token=%s' % (request.session['fbgraph_from_date'], request.session['fb_access_token'])
    
    while flag:
	
	content, endpoint = _retrieveContent(endpoint, client)
	
	#Likely an oAuth exception. Re-try.
	if "error" in content:
	    return redirect('index')
    
	for data in content['data']:
	    
	    # Facebook encodes the returned timestamps in ISO-8601 date-time
	    # format. Following parses it.
	    date = datetime.strptime(data['created_time'][:-5], "%Y-%m-%dT%H:%M:%S") 
	    
	    # If this validates, old data is being seen. Stop processing.
	    if date < date_threshold:
		flag = False
		break
	    
	    # Convert the timestamp from Facebook to the user's timezone.
	    # Facebook timezones are UTC.
	    locale = date.replace(tzinfo=timezone('UTC')).astimezone(timezone(request.session['fbgraph_timezone']))
	    
	    day = locale.weekday()
	    
	    hour = int(locale.strftime("%H"))
    
	    time_matrix[day][hour] = time_matrix[day][hour] + 1	
	    
	    records = records + 1
	    
	    post_frequency[day] = post_frequency[day] + 1
	
	# Exceeded records threshold, stop processing.
	if records >= records_threshold:
	 
	    flag = False
	
	# No more pages of content left from Facebook API.
	if not endpoint:
	    
	    flag = False
	    
    # Convert each day_frequency into a percentage value. A user may not have
    # any records returned (in the time range given) and hence records == 0.
    # Catch the resulting exception.
    try:    
    	day_frequency = [ (val / float(records)) for val in post_frequency.values()]
	
    except ZeroDivisionError:
	day_frequency = [0, 0, 0, 0, 0, 0, 0]
    
    return render_to_response('result.html', locals(),
	                                      context_instance=RequestContext(request))

def sample(request):
    '''
    Render a sample graph with pre-populated data.
    
    Keyword arguments:
    request -- a request object.
    
    Return:
    View with the sample graph.
    '''
    
    FB_LIKE_LINK = settings.FB_LIKE_LINK
    FB_APP_ID = settings.FB_APPID
    
    # Following are all saved data retrieved from a single run of /process.
    records = "489"
    
    from_date_plain = "August, 24, 2012"
    
    to_date_plain = "January, 01, 2012"
    
    time_matrix = "[[6, 3, 4, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 5, 1, 0, 0, 3, 2, 6, 16, 14, 4], [4, 4, 3, 1, 0, 1, 0, 0, 1, 0, 2, 0, 4, 0, 2, 1, 0, 1, 3, 8, 17, 9, 2, 10], [3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 4, 6, 4, 20, 14, 9], [3, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 2, 0, 7, 7, 12, 12, 5, 4], [5, 2, 0, 2, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 2, 4, 1, 6, 8, 17], [9, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 7, 3, 1, 1, 2, 8, 11, 8, 8, 13], [6, 7, 2, 1, 0, 0, 0, 0, 1, 9, 5, 2, 13, 0, 1, 8, 3, 2, 0, 6, 7, 6, 7, 12]]"
    
    day_frequency = "[0.13701431492842536, 0.1492842535787321, 0.13701431492842536, 0.11451942740286299, 0.10633946830265849, 0.1554192229038855, 0.20040899795501022]"
    
    sample = True
    
    return render_to_response('result.html', locals(),
	                                          context_instance=RequestContext(request))