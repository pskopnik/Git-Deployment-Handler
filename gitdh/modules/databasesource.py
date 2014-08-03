# -*- coding: utf-8 -*-

from gitdh.modules import Module

class DatabaseSource(Module):
	def isEnabled(self, action):
		return (action == "cron" and "Database" in self.config)

	def source(self):
		return self.dbBe.getQueuedCommits()
