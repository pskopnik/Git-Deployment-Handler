# -*- coding: utf-8 -*-

class Module(object):
	def __init__(self, conf, args, dbBe):
		self.conf = conf
		self.args = args
		self.dbBe = dbBe

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
