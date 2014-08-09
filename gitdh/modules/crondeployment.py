# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh.gitdhutils import mInsertOnStatus

class CronDeployment(Module):
	def isEnabled(self, action):
		return action == 'postreceive' and not self.dbBe is None

	def postSource(self, commits):
		for commit in commits:
			if self.config.branches.getboolean(commit.branch, 'CronDeployment', False):
				commit.status = 'crondepl_queued'

	def filter(self, commits):
		for commit in commits:
			if commit.status == 'crondepl_queued':
				self._removeCommit(commit)

	def store(self, commits):
		mInsertOnStatus('crondepl_queued', self.dbBe, commits)
