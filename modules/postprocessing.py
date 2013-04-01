from modules.module import Module
import shlex, re, os
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR

class PostProcessing(Module):
	def isEnabled(self, action):
		return True

	def postProcessing(self, commits):
		for commit in commits:
			if hasattr(commit, "deployed") and commit.deployed:
				self.runPostprocessing(commit)

	def runPostprocessing(self, commit):
		confSection = self.conf[commit.branch]
		if "Postprocessing" in confSection:
			postprocCommandString = confSection["Postprocessing"]
			postprocCommands = postprocCommandString.split(" ")
			for postprocCommand in postprocCommands:
				if not postprocCommand + "-command" in self.conf:
					syslog(LOG_ERR, "Command '{0}' doesn't exist".format(postprocCommand))
				else:
					commandSection = self.conf[postprocCommand + "-command"]
					configMode = commandSection["Mode"]
					path = self.conf[commit.branch]["Path"]
					if configMode == "once":
						self.executePathCommand(commandSection["Command"], path, path)
					elif configMode == "perfile":
						files = self.getAllFiles(path)
						if "RegExp" in commandSection:
							files = self.filterFiles(files, commandSection["RegExp"])
						for file in files:
							self.executePathCommand(commandSection["Command"], file, path)

	def getAllFiles(self, path):
		allFiles = []
		pathcontent = os.walk(path)
		for root, dirs, files in pathcontent:
			for file in files:
				allFiles.append(os.path.join(root, file))
		return allFiles

	def filterFiles(self, files, regexp):
		filteredFiles = []
		regexp = re.compile(regexp)
		for file in files:
			if not regexp.search(file) == None:
				filteredFiles.append(file)
		return filteredFiles

	def executePathCommand(self, command, path, basepath):
		command = command.replace("${f}", "'" + path + "'")
		args = shlex.split(command)
		return call(args, stdout=open('/dev/null'), stderr=open('/dev/null'), cwd=basepath)
