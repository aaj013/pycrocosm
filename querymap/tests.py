# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

from querymap.views import p
import pgmap
import random

# Create your tests here.

class ElementsTestCase(TestCase):
	def setUp(self):
		self.username = "john"
		self.password = "glass onion"
		self.email = 'jlennon@beatles.com'
		self.user = User.objects.create_user(self.username, self.email, self.password)
		self.client = Client()
		self.client.login(username=self.username, password=self.password)
		self.roi = [-1.0684204,50.8038735,-1.0510826,50.812877]
		errStr = pgmap.PgMapError()
		ok = p.ResetActiveTables(errStr)
		if not ok:
			print errStr.errStr
		self.assertEqual(ok, True)


	def create_node(self):
		node = pgmap.OsmNode()
		node.objId = -1
		node.metaData.version = 1
		node.metaData.timestamp = 0
		node.metaData.changeset = 1000
		node.metaData.uid = self.user.id
		node.metaData.username = self.user.username.encode("UTF-8")
		node.metaData.visible = True
		node.tags[b"test"] = b"autumn"
		node.lat = 43.0 + random.uniform(-1.0, 1.0)
		node.lon = -70.3 + random.uniform(-1.0, 1.0)

		data = pgmap.OsmData()
		data.nodes.append(node)

		createdNodeIds = pgmap.mapi64i64()
		createdWayIds = pgmap.mapi64i64()
		createdRelationIds = pgmap.mapi64i64()
		errStr = pgmap.PgMapError()

		ok = p.StoreObjects(data, createdNodeIds, createdWayIds, createdRelationIds, errStr)
		if not ok:
			print errStr.errStr
		self.assertEqual(ok, True)
		node.objId = createdNodeIds[-1]
		return node

	def modify_node(self, nodeIn, nodeCurrentVer):
		node = pgmap.OsmNode()
		node.objId = nodeIn.objId
		node.metaData.version = nodeCurrentVer + 1
		node.metaData.timestamp = 0
		node.metaData.changeset = 1000
		node.metaData.uid = self.user.id
		node.metaData.username = self.user.username.encode("UTF-8")
		node.metaData.visible = True
		node.tags[b"test"] = b"winter"
		node.lat = nodeIn.lat + 0.1
		node.lon = nodeIn.lon + 0.2

		data = pgmap.OsmData()
		data.nodes.append(node)

		createdNodeIds = pgmap.mapi64i64()
		createdWayIds = pgmap.mapi64i64()
		createdRelationIds = pgmap.mapi64i64()
		errStr = pgmap.PgMapError()

		ok = p.StoreObjects(data, createdNodeIds, createdWayIds, createdRelationIds, errStr)
		if not ok:
			print errStr.errStr
		self.assertEqual(ok, True)
		return node

	def delete_node(self, nodeIn, nodeCurrentVer):
		node = pgmap.OsmNode()
		node.objId = nodeIn.objId
		node.metaData.version = nodeCurrentVer + 1
		node.metaData.timestamp = 0
		node.metaData.changeset = 1000
		node.metaData.uid = self.user.id
		node.metaData.username = self.user.username.encode("UTF-8")
		node.metaData.visible = False
		node.lat = nodeIn.lat
		node.lon = nodeIn.lon

		data = pgmap.OsmData()
		data.nodes.append(node)

		createdNodeIds = pgmap.mapi64i64()
		createdWayIds = pgmap.mapi64i64()
		createdRelationIds = pgmap.mapi64i64()
		errStr = pgmap.PgMapError()

		ok = p.StoreObjects(data, createdNodeIds, createdWayIds, createdRelationIds, errStr)
		if not ok:
			print errStr.errStr
		self.assertEqual(ok, True)

	def decode_response(self, xml):
		data = pgmap.OsmData()
		dec = pgmap.OsmXmlDecodeString()
		dec.output = data
		for chunk in xml:
			dec.DecodeSubString(chunk, len(chunk), False)
		dec.DecodeSubString(b"", 0, True)
		return data

	def find_object_ids(self, data):
		nodeIdSet = set()
		for nodeNum in range(len(data.nodes)):
			node2 = data.nodes[nodeNum]
			nodeIdSet.add(node2.objId)

		wayIdSet = set()
		nodeMems = set()
		wayMems = set()
		relationMems = set()
		for wayNum in range(len(data.ways)):
			way2 = data.ways[wayNum]
			wayIdSet.add(way2.objId)

			for mem in way2.refs:
				nodeMems.add(mem)

		relationIdSet = set()
		for relationNum in range(len(data.relations)):
			relation2 = data.relations[relationNum]
			relationIdSet.add(relation2.objId)

			for memId, memType in zip(relation2.refIds, relation2.refTypeStrs):
				if memType == "node":
					nodeMems.add(memId)
				if memType == "way":
					wayMems.add(memId)
				if memType == "relation":
					relationMems.add(memId)

		return nodeIdSet, wayIdSet, relationIdSet, nodeMems, wayMems, relationMems

	def get_object_id_dicts(self, data):
		nodeIdDict = {}
		for nodeNum in range(len(data.nodes)):
			node2 = data.nodes[nodeNum]
			nodeIdDict[node2.objId] = node2

		wayIdDict = {}
		for wayNum in range(len(data.ways)):
			way2 = data.ways[wayNum]
			wayIdDict[way2.objId] = way2

		relationIdDict = {}
		for relationNum in range(len(data.relations)):
			relation2 = data.relations[relationNum]
			relationIdDict[relation2.objId] = relation2

		return nodeIdDict, wayIdDict, relationIdDict

	def check_node_in_query(self, node):

		anonClient = Client()
		bbox = [node.lon-0.0001, node.lat-0.0001, node.lon+0.0001, node.lat+0.0001]
		response = anonClient.get(reverse('index') + "?bbox={},{},{},{}".format(*bbox))
		self.assertEqual(response.status_code, 200)

		data = self.decode_response(response.streaming_content)

		nodeIdSet = set()
		for nodeNum in range(len(data.nodes)):
			node2 = data.nodes[nodeNum]
			nodeIdSet.add(node2.objId)
		return node.objId in nodeIdSet
		
	def test_query_active_node(self):
		node = self.create_node()

		found = self.check_node_in_query(node)
		self.assertEqual(found, True)

	def test_modify_active_node(self):
		node = self.create_node()

		modNode = self.modify_node(node, 1)
		self.assertEqual(self.check_node_in_query(modNode), True)
		self.assertEqual(self.check_node_in_query(node), False)

	def test_delete_active_node(self):
		node = self.create_node()

		self.delete_node(node, 1)
		self.assertEqual(self.check_node_in_query(node), False)

	def test_delete_static_node(self):

		#Find a node that is not part of any other object
		anonClient = Client()
		response = anonClient.get(reverse('index') + "?bbox={},{},{},{}".format(*self.roi))
		self.assertEqual(response.status_code, 200)

		data = self.decode_response(response.streaming_content)
		nodeIdSet, wayIdSet, relationIdSet, nodeMems, wayMems, relationMems = self.find_object_ids(data)
		candidateIds = list(nodeIdSet.difference(nodeMems))

		if len(candidateIds) > 0:
			nodeIdDict, wayIdDict, relationIdDict = self.get_object_id_dicts(data)
			nodeObjToDelete = nodeIdDict[candidateIds[0]]

			self.delete_node(nodeObjToDelete, 1)
			self.assertEqual(self.check_node_in_query(nodeObjToDelete), False)
		else:
			print "No free nodes in ROI for testing"

	def test_modify_static_node(self):

		#Find a static node
		anonClient = Client()
		response = anonClient.get(reverse('index') + "?bbox={},{},{},{}".format(*self.roi))
		self.assertEqual(response.status_code, 200)

		data = self.decode_response(response.streaming_content)
		nodeIdSet, wayIdSet, relationIdSet, nodeMems, wayMems, relationMems = self.find_object_ids(data)
		nodeIdSet = list(nodeIdSet)

		if len(nodeIdSet) > 0:
			nodeIdDict, wayIdDict, relationIdDict = self.get_object_id_dicts(data)
			nodeObjToModify = nodeIdDict[nodeIdSet[0]]
			print "nodeObjToModify", nodeObjToModify

			modNode = self.modify_node(nodeObjToModify, 1)
			self.assertEqual(self.check_node_in_query(modNode), True)
			self.assertEqual(self.check_node_in_query(nodeObjToModify), False)

		else:
			print "No nodes in ROI for testing"

	def tearDown(self):
		u = User.objects.get(username = self.username)
		u.delete()
		errStr = pgmap.PgMapError()
		ok = p.ResetActiveTables(errStr)
		if not ok:
			print errStr.errStr
		self.assertEqual(ok, True)

