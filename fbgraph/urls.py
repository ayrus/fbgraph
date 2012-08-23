from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('fbgraph.app.views',
    url(r'^$', 'home'),
    url(r'^connect$', 'connect'),
    url(r'^callback$', 'callback'),
    url(r'^process$', 'process'),
)
