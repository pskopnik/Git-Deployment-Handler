# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh import git
from syslog import syslog, LOG_INFO, LOG_WARNING

class PostReceiveSource(Module):
	def isEnabled(self, action):
		return action == "postreceive"

	def source(self):
		firstCommit = self.args[0]
		lastCommit = self.args[1]
		ref = self.args[2]

		if ref.find("refs/heads/") == 0:
			branch = ref[11:]
		else:
			syslog(LOG_WARNING, "Branch name could not be parsed in '%s'" % (ref,))
			return []

		try:
			self.config.branches[branch]
		except KeyError:
			syslog(LOG_INFO, "No section in config for branch '%s'" % (branch,))
			return []

		gitRepo = git.Git(self.config.repoPath)
		try:
			commits = gitRepo.getLog(since=firstCommit, until=lastCommit, branch=branch)
		except git.GitException as e:
			syslog(LOG_WARNING, "Git log could not be fetched: '%s'" % (e,))
			return []

		for commit in commits:
			commit.status = "deployment_queued"

		return commits
