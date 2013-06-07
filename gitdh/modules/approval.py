# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
from gitdh import gitdhutils

class Approval(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "Approval" in self.conf[commit.branch] and self.conf.getboolean(commit.branch, "Approval"):
				commit.status = "approval"

	def processing(self, commits):
		gitdhutils.mInsertOnStatus("approval", self.dbBe, commits)
