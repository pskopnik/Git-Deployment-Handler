# -*- coding: utf-8 -*-

import os, os.path, importlib
from configparser import ConfigParser
from gitdh.databasebackend import DatabaseBackend
from gitdh.gitdhutils import getConfigBranchSections

def gitDhMain(configFile, action, args, dbBe=None, repositoryName=None, repositoriesDir=None):
	config = ConfigParser()
	config.read(configFile)

	hasGitSection = "Git" in config
	if hasGitSection:
		if "RepositoryName" in config["Git"] and config["Git"]["RepositoryName"] == "AUTO":
			if repositoryName == None:
				raise Exception("Git::RepositoryName == 'AUTO' and no repositoryname given")
			config["Git"]["RepositoryName"] = repositoryName

		if "RepositoriesDir" in config["Git"] and config["Git"]["RepositoriesDir"] == "AUTO":
			if repositoryName == None:
				raise Exception("Git::RepositoriesDir == 'AUTO' and no repositoryname given")
			config["Git"]["RepositoriesDir"] = repositoriesDir


	for section in getConfigBranchSections(config):
		if hasGitSection:
			config[section]["RepositoriesDir"] = config["Git"]["RepositoriesDir"]
		if hasGitSection and "RepositoryName" in config["Git"] and not "RepositoryName" in config[section]:
			config[section]["RepositoryName"] = config["Git"]["RepositoryName"]
		if not "Source" in config[section]:
			config[section]["Source"] = os.path.join(config[section]["RepositoriesDir"], config[section]["RepositoryName"] + '.git')


	if dbBe == None and "Database" in config:
		dbBe = DatabaseBackend.getDatabaseBackend(config=config)

	enabledModules = []

	modulesDir = os.path.join(os.path.dirname(__file__), 'modules')
	for file in os.listdir(modulesDir):
		filePath = os.path.join(modulesDir, file)
		if not file in ("__init__.py", "module.py") and os.path.isfile(filePath) and os.path.splitext(file)[1] == ".py":
			moduleName = os.path.splitext(file)[0]
			module = importlib.import_module("gitdh.modules." + moduleName)
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
