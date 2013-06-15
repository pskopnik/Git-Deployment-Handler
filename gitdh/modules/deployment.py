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
				confSection = self.conf[commit.branch]
				syslog(LOG_INFO, "Pulling commit '{0}'' for branch '{1}'".format(commit.hash, commit.branch))
				rmIntGitFiles = True
				if "RmIntGitFiles" in confSection:
					rmIntGitFiles = confSection.getboolean("RmIntGitFiles")
				gitdhutils.deleteUpdateRepo(confSection["Path"], confSection["RepositoryDir"], commit.branch, rmIntGitFiles=rmIntGitFiles)
				self.dbBe.setStatusFinished(commit)
				commit.deployed = True
