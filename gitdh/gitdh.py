# -*- coding: utf-8 -*-

import os, os.path, importlib
from configparser import ConfigParser
from gitdh.databasebackend import DatabaseBackend


def gitDhMain(configFile, action, args, dbBe=None):
	config = ConfigParser()
	config.read(configFile)

	if dbBe == None:
		dbBe = DatabaseBackend.getDatabaseBackend(config=config)

	modules = __import__("modules")
	enabledModules = []

	for file in os.listdir('modules'):
		if not file in ("__init__.py", "module.py") and os.path.isfile("modules/" + file) and os.path.splitext(file)[1] == ".py":
			moduleName = os.path.splitext(file)[0]
			module = importlib.import_module("modules." + moduleName)
			for moduleAttr in dir(module):
				if moduleAttr.lower() == moduleName:
					moduleClass = getattr(module, moduleAttr)
					module = moduleClass(config, args, dbBe)
					if module.isEnabled(action):
						enabledModules.append(module)

	commits = []

	for module in enabledModules:
		newCommits = module.source()
		if newCommits != None:
			commits += module.source()

	for module in enabledModules:
		module.preProcessing(commits)

	for module in enabledModules:
		module.processing(commits)

	for module in enabledModules:
		module.postProcessing(commits)
