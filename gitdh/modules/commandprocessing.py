# -*- coding: utf-8 -*-

from gitdh.modules import Module
import shlex, re
from os import walk
from os.path import join
from subprocess import check_call, CalledProcessError
from syslog import syslog, LOG_WARNING

try:
	from subprocess import DEVNULL
except ImportError:
	# < Python 3.3 compatibility
	from gitdh.gitdhutils import getDevNull
	DEVNULL = getDevNull()

CONFIG_SECTION_PATTERNS = {'*-command'}

class CommandProcessing(Module):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
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
		configMode = confSect.get('Mode', 'once').lower()
		suppressOutput = confSect.getboolean('SuppressOutput', True)
		shell = confSect.getboolean('Shell', False)
		if configMode == 'once':
			self._executePathCommand(confSect['Command'], path, path, suppressOutput, shell)
		elif configMode == 'file':
			regExpStmt = confSect.get('RegExp', None)
			files = self._getFiles(path, regExpStmt=regExpStmt)
			for file in files:
				self._executePathCommand(confSect['Command'], file, path, suppressOutput, shell)
		else:
			syslog(LOG_WARNING, "Encountered unknown command mode '%s' while running command '%s' on '%s'" % (configMode, command, path))

	def _getFiles(self, path, regExpStmt=None):
		checkRegExp = False
		if regExpStmt is not None:
			checkRegExp = True
			if regExpStmt in self._regExpCache:
				regExp = self._regExpCache[regExpStmt]
			else:
				regExp = re.compile(regExpStmt)
				self._regExpCache[regExpStmt] = regExp

		allFiles = []
		for root, dirs, files in walk(path, topdown=True):
			dirs[:] = [d for d in dirs if not d == '.git']
			for f in files:
				if f[:4] == '.git':
					continue
				path = join(root, f)
				if not checkRegExp or not regExp.search(path) is None:
					allFiles.append(path)
		return allFiles

	def _executePathCommand(self, command, path, basepath, suppressOutput, shell):
		args = command.replace('${f}', "'" + path.replace("'", "\\'") + "'")
		if not shell:
			args = shlex.split(args)
		if suppressOutput:
			return check_call(command, cwd=basepath, stdout=DEVNULL, stderr=DEVNULL, shell=shell)
		else:
			return check_call(command, cwd=basepath, shell=shell)
