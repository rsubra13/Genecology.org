from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

import xml.etree.ElementTree as ET

import urllib2

from locations.models import Location, LocationAuthority

from urlparse import urlparse


def retrieve(request, uri):
    # Determine namespace.
    # http://www.geonames.org/6946760/penglais-campus-university-of-wales-aberystwyth.html
    
    o = urlparse(uri)
    namespace = o.scheme + "://" + o.netloc

    # Try to get LocationAuthority by namespace.
    try:
        authority = LocationAuthority.objects.filter(namespace=namespace).get()
    except ObjectDoesNotExist:
        return HttpResponse("No LocationAuthority defined for namespace {0}" \
                                                 .format(namespace), status=403)
                                                 
    # Check to see if Location is already stored locally.
    try:
        location = Location.objects.filter(uri=uri).get()
    except ObjectDoesNotExist:
        # Retrieve the Location from the LocationAuthority.
        
        id = authority.get_id(uri)
        if id is None:   # Couldn't find an id in the URI.
            return HttpResponse("Malformed Location URI.")
        
        querystring = authority.retrieveformat.format(id)
        response = urllib2.urlopen(authority.host + querystring).read()
        tree = ET.fromstring(response)
        if len(tree) == 0:  # No such Location URI at that Authority.
            raise Http404
        
        lat = tree.findall('.//lat')[0].text
        lng = tree.findall('.//lng')[0].text
        name = tree.findall('.//name')[0].text

        location = Location(uri=uri,
                            name=name,
                            latitude=lat,
                            longitude=lng)
        location.save()

    return HttpResponse(location.id)