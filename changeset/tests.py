# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Changeset

import xml.etree.ElementTree as ET
from defusedxml.ElementTree import parse, fromstring
import StringIO
from xml.sax.saxutils import escape

# Create your tests here.
# alter user microcosm with createdb;
# python manage.py test changeset --keep

class ChangesetTestCase(TestCase):
	def setUp(self):
		self.username = "john"
		self.password = "glass onion"
		self.email = 'jlennon@beatles.com'
		self.user = User.objects.create_user(self.username, self.email, self.password)
		self.client = Client()
		self.client.login(username=self.username, password=self.password)

		self.createXml = """<?xml version='1.0' encoding='UTF-8'?>
		  <osm>
		  <changeset>
			<tag k="created_by" v="JOSM 1.61"/>
			<tag k="comment" v="Just adding some streetnames"/>
		  </changeset>
		</osm>"""

		# Strings from https://www.cl.cam.ac.uk/~mgk25/ucs/examples/quickbrown.txt
		self.unicodeStr = u"Falsches Üben von Xylophonmusik quält jeden größeren Zwerg, Γαζέες καὶ μυρτιὲς δὲν θὰ βρῶ πιὰ στὸ χρυσαφὶ ξέφωτο, Kæmi ný öxi hér ykist þjófum nú bæði víl og ádrepa, イロハニホヘト チリヌルヲ ワカヨタレソ ツネナラム, В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!"
		self.createXmlUnicodeTags = u"""<?xml version='1.0' encoding='UTF-8'?>
		  <osm>
		  <changeset>
			<tag k="source" v="photomapping"/>
			<tag k="comment" v="{}"/>
		  </changeset>
		</osm>""".format(escape(self.unicodeStr))

		self.overlongString = u"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Etiam vulputate quam sit amet arcu efficitur, eget ullamcorper ligula suscipit. Nunc ullamcorper pellentesque libero at lacinia. Donec ut arcu mauris. Quisque ultrices tincidunt pharetra. Morbi indo."
		self.createXmlOverlong = u"""<?xml version='1.0' encoding='UTF-8'?>
		  <osm>
		  <changeset>
			<tag k="source" v="photomapping"/>
			<tag k="comment" v="{}"/>
		  </changeset>
		</osm>""".format(escape(self.overlongString))

		self.expandBboxXml = """<?xml version='1.0' encoding='UTF-8'?>
			<osm version='0.6' upload='true' generator='JOSM'>
			  <node id='-2190' action='modify' visible='true' lat='51.79852581343' lon='-3.38662147656' />
			  <node id='-2193' action='modify' visible='true' lat='50.71917284205' lon='-5.24880409375' />
			  <node id='-2197' action='modify' visible='true' lat='50.29646268337' lon='-4.07326698438' />
			  <node id='-2199' action='modify' visible='true' lat='50.70178040373' lon='-3.08999061719' />
			  <node id='-2201' action='modify' visible='true' lat='51.08292478386' lon='-3.28225135938' />
			  <way id='-2194' action='modify' visible='true'>
				<nd ref='-2190' />
				<nd ref='-2193' />
				<nd ref='-2197' />
				<nd ref='-2199' />
				<nd ref='-2201' />
			  </way>
			</osm>"""

	def test_create_changeset(self):

		response = self.client.put(reverse('create'), self.createXml, content_type='text/xml')

		self.assertEqual(response.status_code, 200)
		cid = int(response.content)
		
		cs = Changeset.objects.get(id = cid)
		self.assertEqual("created_by" in cs.tags, True)
		self.assertEqual("comment" in cs.tags, True)
		self.assertEqual(cs.tags["created_by"] == "JOSM 1.61", True)
		self.assertEqual(cs.tags["comment"] == "Just adding some streetnames", True)

	def test_anon_create_changeset(self):
		anonClient = Client()
		response = anonClient.put(reverse('create'), self.createXml, content_type='text/xml')
		self.assertEqual(response.status_code, 403)

	def test_create_changeset_unicodetags(self):
		response = self.client.put(reverse('create'), self.createXmlUnicodeTags, content_type='text/xml')

		self.assertEqual(response.status_code, 200)
		cid = int(response.content)
		
		cs = Changeset.objects.get(id = cid)
		self.assertEqual("comment" in cs.tags, True)
		self.assertEqual(cs.tags["comment"] == self.unicodeStr, True)

	def test_create_changeset_overlong(self):
		response = self.client.put(reverse('create'), self.createXmlOverlong, content_type='text/xml')

		self.assertEqual(response.status_code, 400)

	def test_get_changeset(self):
		teststr = u"Съешь же ещё этих мягких французских булок да выпей чаю"
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar", 'test': teststr})
		anonClient = Client()

		response = anonClient.get(reverse('changeset', args=(cs.id,)))
		self.assertEqual(response.status_code, 200)
	
		xml = fromstring(response.content)
		self.assertEqual(xml.tag, "osm")
		csout = xml.find("changeset")
		self.assertEqual(int(csout.attrib["id"]) == cs.id, True)
		self.assertEqual("uid" in csout.attrib, True)
		self.assertEqual("created_at" in csout.attrib, True)
		self.assertEqual("min_lon" in csout.attrib, True)
		self.assertEqual("max_lon" in csout.attrib, True)
		self.assertEqual("min_lat" in csout.attrib, True)
		self.assertEqual("max_lat" in csout.attrib, True)

		self.assertEqual(csout.attrib["open"], "true")
		self.assertEqual(len(csout.findall("tag")), 2)
		
		foundFirst, foundSecond = False, False
		for tag in csout.findall("tag"):
			if tag.attrib["k"] == "foo":
				self.assertEqual(tag.attrib["v"], "bar")
				foundFirst = True
			if tag.attrib["k"] == "test":
				self.assertEqual(tag.attrib["v"], teststr)
				foundSecond = True
		self.assertEqual(foundFirst, True)
		self.assertEqual(foundSecond, True)
		self.assertEqual(csout.find("discussion"), None)
		
	def test_get_changeset_missing(self):
		anonClient = Client()
		response = anonClient.get(reverse('changeset', args=(0,)))
		self.assertEqual(response.status_code, 404)

	def test_put_changeset(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar", "man": "child"})

		response = self.client.put(reverse('changeset', args=(cs.id,)), self.createXml, content_type='text/xml')
		self.assertEqual(response.status_code, 200)

		xml = fromstring(response.content)
		self.assertEqual(xml.tag, "osm")
		csout = xml.find("changeset")

		self.assertEqual(len(csout.findall("tag")), 2)
		for tag in csout.findall("tag"):
			if tag.attrib["k"] == "comment":
				self.assertEqual(tag.attrib["v"], "Just adding some streetnames")
			if tag.attrib["k"] == "created_by":
				self.assertEqual(tag.attrib["v"], "JOSM 1.61")

	def test_put_changeset_anon(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar", "man": "child"})

		anonClient = Client()
		response = anonClient.put(reverse('changeset', args=(cs.id,)), self.createXml, content_type='text/xml')
		self.assertEqual(response.status_code, 403)

	def test_close_changeset(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"})

		response = self.client.put(reverse('close', args=(cs.id,)))
		self.assertEqual(response.status_code, 200)

		cs2 = Changeset.objects.get(id=cs.id)
		self.assertEqual(cs2.is_open, False)

	def test_close_changeset_double_close(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"})

		response = self.client.put(reverse('close', args=(cs.id,)))
		self.assertEqual(response.status_code, 200)

		cs2 = Changeset.objects.get(id=cs.id)
		self.assertEqual(cs2.is_open, False)

		response = self.client.put(reverse('close', args=(cs.id,)))
		self.assertEqual(response.status_code, 409)

		self.assertEqual(response.content, "The changeset {} was closed at {}.".format(cs2.id, cs2.close_datetime.isoformat()))

	def test_close_changeset_anon(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"})

		anonClient = Client()
		response = anonClient.put(reverse('close', args=(cs.id,)))
		self.assertEqual(response.status_code, 403)

		cs2 = Changeset.objects.get(id=cs.id)
		self.assertEqual(cs2.is_open, True)

	def test_expand_bbox(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"})

		response = self.client.post(reverse('expand_bbox', args=(cs.id,)), self.expandBboxXml, 
			content_type='text/xml')
		self.assertEqual(response.status_code, 200)

		cs2 = Changeset.objects.get(id=cs.id)
		self.assertEqual(cs2.bbox_set, True)
		self.assertEqual(abs(cs2.min_lat - 50.2964626834) < 1e-6, True) 
		self.assertEqual(abs(cs2.max_lat - 51.7985258134) < 1e-6, True) 
		self.assertEqual(abs(cs2.min_lon + 3.08999061719) < 1e-6, True) 
		self.assertEqual(abs(cs2.max_lon + 5.24880409375) < 1e-6, True)

		xml = fromstring(response.content)
		self.assertEqual(xml.tag, "osm")
		csout = xml.find("changeset")
		self.assertEqual(int(csout.attrib["id"]) == cs.id, True)
		self.assertEqual(abs(float(csout.attrib["min_lat"]) - 50.2964626834) < 1e-6, True)
		self.assertEqual(abs(float(csout.attrib["max_lat"]) - 51.7985258134) < 1e-6, True)
		self.assertEqual(abs(float(csout.attrib["min_lon"]) + 3.08999061719) < 1e-6, True)
		self.assertEqual(abs(float(csout.attrib["max_lon"]) + 5.24880409375) < 1e-6, True)

	def test_expand_bbox_anon(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"})

		anonClient = Client()
		response = anonClient.post(reverse('expand_bbox', args=(cs.id,)), self.expandBboxXml, 
			content_type='text/xml')
		self.assertEqual(response.status_code, 403)

	def test_expand_bbox_closed(self):
		cs = Changeset.objects.create(user=self.user, tags={"foo": "bar"}, is_open=False)

		response = self.client.post(reverse('expand_bbox', args=(cs.id,)), self.expandBboxXml, 
			content_type='text/xml')
		self.assertEqual(response.status_code, 409)

		self.assertEqual(response.content, "The changeset {} was closed at {}.".format(cs.id, cs.close_datetime.isoformat()))

	def test_upload_single_node(self):

		cs = Changeset.objects.create(user=self.user, tags={"foo": "invade"}, is_open=True)

		xml = """<osmChange generator="JOSM" version="0.6">
		<create>
		  <node changeset="{}" id="-5393" lat="50.79046578105" lon="-1.04971367626" />
		</create>
		</osmChange>""".format(cs.id)

		response = self.client.post(reverse('upload', args=(cs.id,)), xml, 
			content_type='text/xml')
		if response.status_code != 200:
			print response.content
		self.assertEqual(response.status_code, 200)

	def tearDown(self):
		u = User.objects.get(username = self.username)
		u.delete()

