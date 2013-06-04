# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
import gitdh.gitdhutils

class CronDeployment(Module):
	def isEnabled(self, action):
		return (action == "postreceive")

	def preProcessing(self, commits):
		for commit in commits:
			if "CronDeployment" in self.conf[commit.branch] and self.conf.getboolean(commit.branch, "CronDeployment"):
				commit.status = "crondepl_queued"
				commit.preventDepl = True

	def processing(self, commits):
		gitdhutils.mInsertOnStatus("crondepl_queued", self.dbBe, commits)
