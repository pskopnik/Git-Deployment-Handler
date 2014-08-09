# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh import gitdhutils

class DatabaseLog(Module):
	def isEnabled(self, action):
		return action == 'postreceive' and not self.dbBe is None

	def postSource(self, commits):
		for commit in commits:
			if self.config.branches.getboolean(commit.branch, 'DatabaseLog', False):
				commit.status = 'databaselog_queued'

	def store(self, commits):
		commits = gitdhutils.filterOnStatusBase('databaselog', commits)
		gitdhutils.mInsertCommit(self.dbBe, commits)
