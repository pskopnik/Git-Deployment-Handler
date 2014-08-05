# -*- coding: utf-8 -*-
import os.path, os
from importlib import import_module

class Module(object):
	def __init__(self, config, args, dbBe):
		self.config = config
		self.args = args
		self.dbBe = dbBe

	def isEnabled(self, action):
		pass

	def source(self):
		return []

	def preProcessing(self, commits):
		pass

	def processing(self, commits):
		pass

	def postProcessing(self, commits):
		pass

class ModuleLoader(object):
	def __init__(self, modulesDir=None):
		if modulesDir == None:
			self.modulesDir = os.path.join(os.path.dirname(__file__), 'modules')
		else:
			self.modulesDir = modulesDir

	def getModules(self):
		modules = []
		for file in os.listdir(self.modulesDir):
			filePath = os.path.join(self.modulesDir, file)
			if not file == '__init__.py' and os.path.isfile(filePath) and os.path.splitext(file)[1] == '.py':
				moduleName = os.path.splitext(file)[0]
				module = import_module('gitdh.modules.' + moduleName)
				modules.append(module)
		return modules

	def getModuleClasses(self):
		moduleClasses = []
		modules = self.getModules()
		for module in modules:
			mdNm = module.__name__
			moduleName = mdNm[mdNm.rfind('.') + 1:]
			for moduleAttr in dir(module):
				if moduleAttr.lower() == moduleName.lower():
					moduleClasses.append(getattr(module, moduleAttr))
		return moduleClasses

	def getModuleObjects(self, *args, **kwargs):
		moduleObjects = []
		moduleClasses = self.getModuleClasses()
		for moduleClass in moduleClasses:
			moduleObjects.append(moduleClass(*args, **kwargs))
		return moduleObjects



