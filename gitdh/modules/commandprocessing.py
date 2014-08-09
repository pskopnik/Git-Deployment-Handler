# -*- coding: utf-8 -*-

from gitdh.modules import Module
import shlex, re, os
from os.path import join
from subprocess import check_call, CalledProcessError
from syslog import syslog, LOG_WARNING

CONFIG_SECTION_PATTERNS = {'*-command'}

class CommandProcessing(Module):
	def __init__(self):
		super().__init__()
		self._regExpCache = {}

	def isEnabled(self, action):
		return True

	def preProcess(self, commits):
		self._runProcessing('Preprocessing', commits)

	def postProcess(self, commits):
		self._runProcessing('Postprocessing', commits)

	def _runProcessing(self, procType, commits):
		for commit in commits:
			confSection = self.config.branches[commit.branch]
			path = confSection["Path"]
			if procType in confSection:
				for procCommand in confSection[procType].split(" "):
					try:
						self._runCommand(procCommand, path)
					except CalledProcessError as e:
						syslog(LOG_WARNING, "Error while running '%s':'%s' for commit '%s': %s" % (procType, procCommand, commit, e))

	def _runCommand(self, command, path):
		if not command + '-command' in self.config:
			syslog(LOG_WARNING, "Command '%s' doesn't exist in config" % (command,))
			return

		confSect = self.config[command + '-command']
		configMode = confSect.get('Mode', 'once')
		suppressOutput = confSect.get('SuppressOutput', True)
		if configMode == 'once':
			self._executePathCommand(confSect['Command'], path, path, suppressOutput)
		elif configMode == 'perfile':
			regExpStmt = confSect.get('RegExp', None)
			files = self._getFiles(path, regExpStmt=regExpStmt)
			for file in files:
				self._executePathCommand(confSect['Command'], file, path, suppressOutput)

	def _getFiles(self, path, regExpStmt=None):
		checkRegExp = False
		if not regExpStmt is None:
			checkRegExp = True
			if regExpStmt in self._regExpCache:
				regExp = self._regExpCache[regExpStmt]
			else:
				regExp = re.compile(regExpStmt)
				self._regExpCache[regExpStmt] = regExp

		allFiles = []
		for root, dirs, files in os.walk(path):
			for file in files:
				path = join(root, file)
				if not checkRegExp or not regExp.search(path) is None:
					allFiles.append(path)
		return allFiles

	def _executePathCommand(self, command, path, basepath, suppressOutput):
		command = command.replace('${f}', "'" + path + "'")
		args = shlex.split(command)
		if suppressOutput:
			with open(os.devnull, mode='w') as fd:
				return check_call(args, cwd=basepath, stdout=fd, stderr=fd)
		else:
			return check_call(args, cwd=basepath)
