# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import UserData, UserPreferences

import xml.etree.ElementTree as ET
from defusedxml.ElementTree import parse
import cStringIO

# Create your views here.

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def details(request):

	userRecord = request.user

	root = ET.Element('osm')
	doc = ET.ElementTree(root)
	root.attrib["version"] = str(settings.API_VERSION)
	root.attrib["generator"] = settings.GENERATOR

	user = ET.SubElement(root, "user")
	user.attrib["display_name"] = userRecord.username
	user.attrib["account_created"] = str(userRecord.date_joined.isoformat())
	user.attrib["id"] = str(userRecord.userdata.mapid)

	cts = ET.SubElement(user, "contributor-terms")
	cts.attrib["agreed"] = "false"
	cts.attrib["pd"] = "false"

	roles = ET.SubElement(user, "roles")

	changesets = ET.SubElement(user, "changesets")
	changesets.attrib["count"] = "12345"

	traces = ET.SubElement(user, "traces")
	traces.attrib["count"] = "12345"

	blocks = ET.SubElement(user, "blocks")
	received = ET.SubElement(blocks, "received")
	received.attrib["count"] = "0"
	received.attrib["active"] = "0"

	if userRecord.userdata.home_zoom >= 0:
		home = ET.SubElement(user, "home")
		home.attrib["lat"] = str(userRecord.userdata.home_lat)
		home.attrib["lon"] = str(userRecord.userdata.home_lon)
		home.attrib["zoom"] = str(userRecord.userdata.home_zoom)

	description = ET.SubElement(user, "description")
	description.text = userRecord.userdata.description

	languages = ET.SubElement(user, "languages")
	lang = ET.SubElement(languages, "lang")
	lang.text="en"

	messages = ET.SubElement(user, "messages")
	msgReceived = ET.SubElement(messages, "received")
	msgReceived.attrib["count"] = "1"
	msgReceived.attrib["unread"] = "0"
	msgSent = ET.SubElement(messages, "sent")
	msgSent.attrib["count"] = "1"

	sio = cStringIO.StringIO()
	doc.write(sio, "utf8")
	return HttpResponse(sio.getvalue(), content_type='text/xml')

@csrf_exempt
@api_view(['GET', 'PUT'])
@permission_classes((IsAuthenticated, ))
def preferences(request):

	userRecord = request.user
	prefs = UserPreferences.objects.filter(user=userRecord)

	if request.method == 'GET':
		root = ET.Element('osm')
		doc = ET.ElementTree(root)
		root.attrib["version"] = str(settings.API_VERSION)
		root.attrib["generator"] = settings.GENERATOR

		preferences = ET.SubElement(root, "preferences")

		for pref in prefs:
			preference = ET.SubElement(preferences, "preference")
			preference.attrib["k"] = pref.key
			preference.attrib["v"] = pref.value

		sio = cStringIO.StringIO()
		doc.write(sio, "utf8")
		return HttpResponse(sio.getvalue(), content_type='text/xml')

	if request.method == 'PUT':
		return HttpResponse("", content_type='text/plain')

@csrf_exempt
@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def preferences_put(request, key):
	return HttpResponse("", content_type='text/plain')

