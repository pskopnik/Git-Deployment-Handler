# -*- coding: utf-8 -*-

from modules.module import Module
from syslog import syslog, LOG_ERR, LOG_INFO
import gitdhutils

class Deployment(Module):
	def isEnabled(self, action):
		return True

	def processing(self, commits):
		for commit in commits:
			if commit.status != None and "_" in commit.status and commit.status[commit.status.rfind('_') + 1:] == "queued" and not (hasattr(commit, "preventDepl") and commit.preventDepl):
				self.dbCon.setStatusWorking(commit)
				confSection = self.conf[commit.branch]
				syslog(LOG_INFO, "Pulling commit '{0}'' for branch '{1}'".format(commit.hash, commit.branch))
				gitdhutils.deleteUpdateRepo(confSection["Path"], confSection["Repositoryname"], commit.branch, self.conf["Git"]["RepositoriesDir"])
				self.dbCon.setStatusFinished(commit)
				commit.deployed = True
