import unittest, tempfile
from gitdh.modules.external import TmpOrigFile

class TmpOrigFileTestCase(unittest.TestCase):

	def setUp(self):
		self.f = tempfile.NamedTemporaryFile()
		self.f.write("ORIGINAL".encode())
		self.f.flush()
		self.f.seek(0)

	def test_tmpOrigFile(self):
		filePath = self.f.name

		t1 = TmpOrigFile(filePath, postfix="ORIG.TEST")
		t1.create()
		with open(filePath, 'w') as f:
			f.write("t1")
		with open(filePath + ".ORIG.TEST.1", 'r') as f:
			content = f.read()
			self.assertEqual(content, "ORIGINAL")

		t2 = TmpOrigFile(filePath, postfix="ORIG.TEST")
		t2.create()
		with open(filePath, 'w') as f:
			f.write("t2")
		with open(filePath + ".ORIG.TEST.2", 'r') as f:
			content = f.read()
			self.assertEqual(content, "t1")

		t3 = TmpOrigFile(filePath, postfix="ORIG.TEST")
		t3.create()
		with open(filePath, 'w') as f:
			f.write("t3")
		with open(filePath + ".ORIG.TEST.3", 'r') as f:
			content = f.read()
			self.assertEqual(content, "t2")

		t2.remove()
		with open(filePath + ".ORIG.TEST.1", 'r') as f:
			content = f.read()
			self.assertEqual(content, "ORIGINAL")
		with open(filePath + ".ORIG.TEST.3", 'r') as f:
			content = f.read()
			self.assertEqual(content, "t1")

		t1.remove()
		with open(filePath + ".ORIG.TEST.3", 'r') as f:
			content = f.read()
			self.assertEqual(content, "ORIGINAL")

		t3.remove()

		with open(filePath, 'r') as f:
			content = f.read()
			self.assertEqual(content, "ORIGINAL")

