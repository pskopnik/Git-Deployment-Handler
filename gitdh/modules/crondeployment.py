# -*- coding: utf-8 -*-

from gitdh.modules.module import Module
from gitdh import gitdhutils

class CronDeployment(Module):
	def isEnabled(self, action):
		return (action == "postreceive" and "Database" in self.config)

	def preProcessing(self, commits):
		for commit in commits:
			if "CronDeployment" in self.config[commit.branch] and self.config.getboolean(commit.branch, "CronDeployment"):
				commit.status = "crondepl_queued"
				commit.preventDepl = True

	def processing(self, commits):
		gitdhutils.mInsertOnStatus("crondepl_queued", self.dbBe, commits)
