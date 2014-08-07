# -*- coding: utf-8 -*-

from gitdh.config import Config
from gitdh.database import DatabaseBackend
from gitdh.module import ModuleLoader, Commit

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

	commitCycle(enabledModules)

def commitCycle(modules):
	inptCommits = []
	commits = []
	removedCommits = []
	passedCommits = []

	for module in modules:
		inptCommits += module.source()

	for inptCommit in inptCommits:
		if isinstance(inptCommit, Commit):
			commits.append(inptCommit)
		else:
			commits.append(Commit.fromGitCommit(inptCommit))

	for module in modules:
		module.filter(commits)

	for commit in commits:
		if commit.removed:
			removedCommits.append(commit)
		else:
			passedCommits.append(commit)

	for module in modules:
		module.processRemoved(removedCommits)

	for module in modules:
		module.preProcess(passedCommits)

	for module in modules:
		module.process(passedCommits)

	for module in modules:
		module.postProcess(passedCommits)

	for module in modules:
		module.store(commits)
