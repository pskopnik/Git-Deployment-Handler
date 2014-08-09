# -*- coding: utf-8 -*-
import os.path, os, re
import gitdh.git
from importlib import import_module

class Module(object):
	def __init__(self, config, args, dbBe):
		self.config = config
		self.args = args
		self.dbBe = dbBe

	def isEnabled(self, action):
		return False

	def source(self):
		return []

	def postSource(self, commits):
		pass

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

	def _removeCommit(self, commit):
		commit.remove(self)

class Commit(gitdh.git.GitCommit):
	@staticmethod
	def fromGitCommit(gitCommit):
		c = Commit()
		c.__dict__.update(gitCommit.__dict__)
		return c

	def __init__(self):
		super().__init__(None, None, None, None, None, None)
		self.removed = False
		self.removers = []

	def remove(self, module):
		self.removed = True
		self.removers.append(module)

	def __str__(self):
		if self.hash is None:
			return ''
		return self.hash

class ModuleLoader(object):
	_objCache = {}

	def __new__(cls, modulesDir=None):
		if modulesDir in ModuleLoader._objCache:
			return ModuleLoader._objCache[None]
		else:
			obj = super().__new__(cls)
			ModuleLoader._objCache[modulesDir] = obj
			return obj

	def __init__(self, modulesDir=None):
		self.clearCache()
		self._baseConfSects = {
			'gitdh.config': ({'DEFAULT'}, set()),
			'gitdh.git': ({'Git'}, set()),
			'gitdh.database': ({'Database'}, set())
		}

		if modulesDir is None:
			self.modulesDir = os.path.join(os.path.dirname(__file__), 'modules')
		else:
			self.modulesDir = modulesDir

	def clearCache(self):
		self._modules = None
		self._moduleClasses = None
		self._moduleConfTuples = None
		self._confSects = None
		self._confRegEx = None
		self._confPatRegEx = None

	def getModules(self):
		if not self._modules is None:
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
		if not self._moduleClasses is None:
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

	def getModuleConfTuples(self):
		if self._moduleConfTuples is None:
			self._moduleConfTuples = self._fetchModConfSects()
		return self._moduleConfTuples

	def getModuleConfTuple(self, module):
		return self.getModuleConfTuples().get(module, (set(), set()))

	def getConfSects(self):
		if not self._confSects is None:
			return self._confSects

		moduleConfSects = self.getModuleConfTuples()
		confSects = set()
		for sections, patterns in moduleConfSects.values():
			confSects = confSects.union(sections)

		self._confSects = confSects
		return confSects

	def getConfRegEx(self):
		if self._confRegEx is None:
			self._confRegEx = self._genSectRegEx()

		return self._confRegEx

	def getConfPatRegEx(self):
		if self._confPatRegEx is None:
			self._confPatRegEx = self._genSectRegEx(patOnly=True)

		return self._confPatRegEx

	def _fetchModConfSects(self):
		modules = self.getModules()
		modConfSects = self._baseConfSects
		for module in modules:
			sections = set()
			patterns = set()
			if hasattr(module, 'CONFIG_SECTIONS'):
				sections = set(module.CONFIG_SECTIONS)
			if hasattr(module, 'CONFIG_SECTION_PATTERNS'):
				patterns = set(module.CONFIG_SECTION_PATTERNS)
			if not (len(sections) == 0 and len(patterns) == 0):
				modConfSects[module.__name__] = (sections, patterns)
		return modConfSects

	def _genSectRegEx(self, patOnly=False):
		regExpStmt = '^('
		first = True
		for sections, patterns in self.getModuleConfTuples().values():
			if not patOnly:
				for section in sections:
					if first:
						first = False
					else:
						regExpStmt += '|'
					regExpStmt += re.escape(section)
			for pattern in patterns:
				if first:
					first = False
				else:
					regExpStmt += '|'
				regExpStmt += re.escape(pattern).replace('\\*', '.*')
		regExpStmt += ')$'
		regExp = re.compile(regExpStmt)
		return regExp
