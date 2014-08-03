# -*- coding: utf-8 -*-

from gitdh.modules import Module
from gitdh import gitdhutils

class Approval(Module):
	def isEnabled(self, action):
		return (action == "postreceive" and "Database" in self.config)

	def preProcessing(self, commits):
		for commit in commits:
			if "Approval" in self.config[commit.branch] and self.config.getboolean(commit.branch, "Approval"):
				commit.status = "approval"

	def processing(self, commits):
		gitdhutils.mInsertOnStatus("approval", self.dbBe, commits)
