class Module(object):
	def __init__(self, conf, args, dbCon):
		self.conf = conf
		self.args = args
		self.dbCon = dbCon

	def isEnabled(self, action):
		pass

	def source(self):
		pass

	def preProcessing(self, commits):
		pass

	def processing(self, commits):
		pass

	def postProcessing(self, commits):
		pass
