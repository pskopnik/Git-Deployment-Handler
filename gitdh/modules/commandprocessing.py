# -*- coding: utf-8 -*-

from gitdh.modules import Module
import shlex, re, os
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR

class CommandProcessing(Module):
	def isEnabled(self, action):
		return True

	def preProcessing(self, commits):
		for commit in commits:
			if not (hasattr(commit, "preventDepl") and commit.preventDepl):
				self._runProcessing('Preprocessing', commit)

	def postProcessing(self, commits):
		for commit in commits:
			if hasattr(commit, 'deployed') and commit.deployed:
				self._runProcessing('Postprocessing', commit)

	def _runProcessing(self, procType, commit):
		confSection = self.config[commit.branch]
		if procType in confSection:
			for procCommand in confSection[procType].split(" "):
				try:
					self._runCommand(procCommand, confSection)
				except CalledProcessError as e:
					syslog(LOG_ERR, e)

	def _runCommand(self, command, confSection):
		if not command + '-command' in self.config:
			syslog(LOG_ERR, "Command '{0}' doesn't exist".format(command))
			return

		commandSection = self.config[command + '-command']
		configMode = commandSection['Mode']
		path = confSection['Path']
		if configMode == 'once':
			self._executePathCommand(commandSection['Command'], path, path)
		elif configMode == 'perfile':
			files = self._getAllFiles(path)
			if 'RegExp' in commandSection:
				files = self._filterFiles(files, commandSection['RegExp'])
			for file in files:
				self._executePathCommand(commandSection['Command'], file, path)

	def _getAllFiles(self, path):
		allFiles = []
		pathcontent = os.walk(path)
		for root, dirs, files in pathcontent:
			for file in files:
				allFiles.append(os.path.join(root, file))
		return allFiles

	def _filterFiles(self, files, regexp):
		filteredFiles = []
		regexp = re.compile(regexp)
		for file in files:
			if not regexp.search(file) == None:
				filteredFiles.append(file)
		return filteredFiles

	def _executePathCommand(self, command, path, basepath):
		command = command.replace('${f}', "'" + path + "'")
		args = shlex.split(command)
		return call(args, stdout=open(os.devnull), stderr=open(os.devnull), cwd=basepath)
