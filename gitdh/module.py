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

	def filter(self, commits):
		pass

	def processRemoved(self, commits):
		pass

	def preProcess(self, commits):
		pass

	def process(self, commits):
		pass

	def postProcess(self, commits):
		pass

	def store(self, commits):
		pass

class ModuleLoader(object):
	_objCache = {}

	def __new__(cls, modulesDir=None):
		if modulesDir in ModuleLoader._objCache:
			return ModuleLoader._objCache[None]
		else:
			obj = super().__new__(cls, modulesDir)
			ModuleLoader._objCache[modulesDir] = obj
			return obj

	def __init__(self, modulesDir=None):
		self._modules = None
		self._moduleClasses = None
		if modulesDir == None:
			self.modulesDir = os.path.join(os.path.dirname(__file__), 'modules')
		else:
			self.modulesDir = modulesDir

	def getModules(self):
		if not self._modules == None:
			return self._modules

		self._modules = []
		for file in os.listdir(self.modulesDir):
			filePath = os.path.join(self.modulesDir, file)
			if not file == '__init__.py' and os.path.isfile(filePath) and os.path.splitext(file)[1] == '.py':
				moduleName = os.path.splitext(file)[0]
				module = import_module('gitdh.modules.' + moduleName)
				self._modules.append(module)
		return self._modules

	def getModuleClasses(self):
		if not self._moduleClasses == None:
			return self._moduleClasses

		self._moduleClasses = []
		for module in self.getModules():
			mdNm = module.__name__
			moduleName = mdNm[mdNm.rfind('.') + 1:]
			for moduleAttr in dir(module):
				if moduleAttr.lower() == moduleName.lower():
					self._moduleClasses.append(getattr(module, moduleAttr))
		return self._moduleClasses

	def initModuleObjects(self, *args, **kwargs):
		moduleObjects = []
		for moduleClass in self.getModuleClasses():
			moduleObjects.append(moduleClass(*args, **kwargs))
		return moduleObjects

	def clearCache(self):
		self._modules = None
		self._moduleClasses = None

