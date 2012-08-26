from django.conf.urls import patterns, include, url

urlpatterns = patterns('fbgraph.app.views',
    url(r'^$', 'home', name="index"),
    url(r'^callback$', 'callback', name="callback"),
    url(r'^process$', 'process', name="process"),
    url(r'^sample$', 'sample', name="sample"),
)
