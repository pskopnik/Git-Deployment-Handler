# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
from syslog import syslog, LOG_ERR, LOG_INFO
from gitdh import gitdhutils

class Deployment(Module):
	def isEnabled(self, action):
		return True

	def processing(self, commits):
		for commit in commits:
			if commit.status != None and "_" in commit.status and commit.status[commit.status.rfind('_') + 1:] == "queued" and not (hasattr(commit, "preventDepl") and commit.preventDepl):
				self.dbBe.setStatusWorking(commit)
				configSection = self.config[commit.branch]
				syslog(LOG_INFO, "Deploying commit '{0}' from '{1}' : '{2}'".format(commit.hash, commit.repository, commit.branch))
				rmIntGitFiles = True
				if "RmIntGitFiles" in configSection:
					rmIntGitFiles = configSection.getboolean("RmIntGitFiles")
				if not hasattr(commit, "deploymentSource"): commit.deploymentSource = configSection["Source"]
				gitdhutils.deleteUpdateRepo(configSection["Path"], commit.deploymentSource, commit.branch, rmIntGitFiles=rmIntGitFiles)
				self.dbBe.setStatusFinished(commit)
				commit.deployed = True
