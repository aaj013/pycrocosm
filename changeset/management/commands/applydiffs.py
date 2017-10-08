from django.core.management.base import BaseCommand, CommandError
from changeset.views import upload_update_diff_result
import os
import gzip
import pgmap
from querymap.views import p

class Command(BaseCommand):
	help = 'Apply diffs to database'

	def add_arguments(self, parser):
		#parser.add_argument('poll_id', nargs='+', type=int)
		pass

	def handle(self, *args, **options):

		diffFolder = "/home/tim/Desktop/diffs"
		
		for root, dirs, files in os.walk(diffFolder):

			for fina in files:
				ext = os.path.splitext(fina)[-1]
				if ext != '.gz': continue
				fullFina = os.path.join(root, fina)
				print fullFina
				xml = gzip.open(fullFina)

				t = p.GetTransaction(b"EXCLUSIVE")

				#Decode XML
				data = pgmap.OsmChange()
				dec = pgmap.OsmChangeXmlDecodeString()
				dec.output = data
				pageSize = 100000
				while True:
					inputXml = xml.read(pageSize)
					if len(inputXml) == 0:
						break
					dec.DecodeSubString(inputXml, len(inputXml), False)
				dec.DecodeSubString("".encode("UTF-8"), 0, True)
				if not dec.parseCompletedOk:
					raise ParseError(detail=dec.errString)

				for i in range(data.blocks.size()):
					action = data.actions[i]
					block = data.blocks[i]

					createdNodeIds = pgmap.mapi64i64()
					createdWayIds = pgmap.mapi64i64()
					createdRelationIds = pgmap.mapi64i64()
					errStr = pgmap.PgMapError()

					ok = t.StoreObjects(block, createdNodeIds, createdWayIds, createdRelationIds, errStr)
					if not ok:
						print errStr.errStr
						return

				t.Commit()

