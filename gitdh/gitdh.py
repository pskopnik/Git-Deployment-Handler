# -*- coding: utf-8 -*-

from gitdh.config import Config
from gitdh.database import DatabaseBackend
from gitdh.module import ModuleLoader

def gitDhMain(target, action, args, dbBe=None):
	config = Config.fromPath(target)

	if config.repoPath == None:
		raise Exception("Missing RepositoryPath in '%s'" % (target,))

	for branchSection in config.branches:
		if not 'Source' in config[branchSection]:
			config[branchSection]['Source'] = config.repoPath

	if dbBe == None and 'Database' in config:
		dbBe = DatabaseBackend.getDatabaseBackend(config=config)

	enabledModules = []

	modules = ModuleLoader.initModuleObjects(config, args, dbBe)
	for module in modules:
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
