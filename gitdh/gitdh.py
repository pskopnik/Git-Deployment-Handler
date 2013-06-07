# -*- coding: utf-8 -*-

import os, os.path, importlib
from configparser import ConfigParser
from gitdh.databasebackend import DatabaseBackend


def gitDhMain(configFile, action, args, dbBe=None, repositoryName=None, repositoriesDir=None):
	config = ConfigParser()
	config.read(configFile)

	if "RepositoryName" in config["Git"] and config["Git"]["RepositoryName"] == "AUTO":
		if repositoryName == None:
			raise Exception("Git::RepositoryName == 'AUTO' and no repositoryname given")
		config["Git"]["RepositoryName"] = repositoryName

	if "RepositoriesDir" in config["Git"] and config["Git"]["RepositoriesDir"] == "AUTO":
		if repositoryName == None:
			raise Exception("Git::RepositoriesDir == 'AUTO' and no repositoryname given")
		config["Git"]["RepositoriesDir"] = repositoriesDir

	if "RepositoryName" in config["Git"]:
		for section in config:
			if not section in ["Git", "DEFAULT", "Database"] and not ("-" in section and section[section.rfind('-') + 1:] == "command"):
				if not "RepositoryName" in config[section]:
					config[section]["RepositoryName"] = config["Git"]["RepositoryName"]

	if dbBe == None:
		dbBe = DatabaseBackend.getDatabaseBackend(config=config)

	gitdh = __import__("gitdh.modules")
	modules = gitdh.modules
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
			commits += module.source()

	for module in enabledModules:
		module.preProcessing(commits)

	for module in enabledModules:
		module.processing(commits)

	for module in enabledModules:
		module.postProcessing(commits)
