# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh.gitdhutils import mInsertOnStatus

class Approval(Module):
	def isEnabled(self, action):
		return action == 'postreceive' and not self.dbBe is None

	def postSource(self, commits):
		for commit in commits:
			if self.config.branches.getboolean(commit.branch, 'Approval', False):
				commit.status = 'approval'

	def filter(self, commits):
		for commit in commits:
			if commit.status == 'approval':
				self._removeCommit(commit)

	def store(self, commits):
		mInsertOnStatus('approval', self.dbBe, commits)
