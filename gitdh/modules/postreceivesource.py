# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
import git
from syslog import syslog, LOG_ERR, LOG_INFO

class PostReceiveSource(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def source(self):
		firstCommit = self.args[0]
		lastCommit = self.args[1]
		ref = self.args[2]

		if ref.find("refs/heads/") == 0:
			branch = ref[11:]
		else:
			syslog(LOG_ERR,  "Branch name could not be parsed in '{0}'".format(ref))
			return []

		if not branch in self.conf:
			syslog(LOG_ERR, "No section in config for branch '{0}'".format(branch))
			return []

		gitRepo = git.Git(self.conf[branch]["Repositoryname"], repositoriesDir=self.conf["Git"]["RepositoriesDir"])
		commits = gitRepo.getLog(since=firstCommit, until=lastCommit, branch=branch)

		for commit in commits:
			commit.status = "deployment_queued"

		return commits
