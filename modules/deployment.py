from modules.module import Module
from syslog import syslog, LOG_ERR, LOG_INFO
import gprhutils

class Deployment(Module):
	def isEnabled(self, action):
		return true

	def processing(self, commits):
		for commit in commits:
			if commit.status != None and "_" in commit.status and commit.status[commit.status.rfind('_') + 1:] == "queued":
				self.dbCon.setStatusWorking(commit)
				confSection = self.conf[commit.branch]
				syslog(LOG_INFO, "Pulling git for '{0}'".format(branch))
				gprhutils.deleteUpdateRepo(confSection["Path"], confSection["Repositoryname"], branch, self.conf["Git"]["RepositoriesDir"])
				self.dbCon.setStatusFinished(commit)
