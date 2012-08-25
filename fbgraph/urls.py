from django.conf.urls import patterns, include, url

urlpatterns = patterns('fbgraph.app.views',
    url(r'^$', 'home'),
    url(r'^callback$', 'callback'),
    url(r'^process$', 'process'),
    url(r'^sample$', 'sample'),
)
