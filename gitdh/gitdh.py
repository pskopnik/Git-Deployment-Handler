# -*- coding: utf-8 -*-

import os, os.path, importlib
from gitdh.config import Config
from gitdh.databasebackend import DatabaseBackend

def gitDhMain(target, action, args, dbBe=None):
	config = Config.fromPath(target)

	if not 'Git' in config or not 'RepositoryPath' in config['Git']:
		raise Exception("Missing RepositoryPath in '%s'" % (target,))

	for branchSection in config.branches:
		if not 'Source' in config[branchSection]:
			config[branchSection]['Source'] = config['Git']['RepositoryPath']

	if dbBe == None and 'Database' in config:
		dbBe = DatabaseBackend.getDatabaseBackend(config=config)

	enabledModules = []

	modulesDir = os.path.join(os.path.dirname(__file__), 'modules')
	for file in os.listdir(modulesDir):
		filePath = os.path.join(modulesDir, file)
		if not file in ('__init__.py', 'module.py') and os.path.isfile(filePath) and os.path.splitext(file)[1] == '.py':
			moduleName = os.path.splitext(file)[0]
			module = importlib.import_module('gitdh.modules.' + moduleName)
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
			commits += newCommits

	for module in enabledModules:
		module.preProcessing(commits)

	for module in enabledModules:
		module.processing(commits)

	for module in enabledModules:
		module.postProcessing(commits)
