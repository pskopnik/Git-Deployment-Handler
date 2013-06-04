# -*- coding: utf-8 -*-

from modules.module import Module

class DatabaseSource(Module):
	def isEnabled(self, action):
		return (action == "cron")

	def source(self):
		return self.dbBe.getQueuedCommits()
