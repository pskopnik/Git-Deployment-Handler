# -*- coding: utf-8 -*-

from gitdh import git
from collections import Mapping
from configparser import ConfigParser
import os.path

class Config(ConfigParser):

	@staticmethod
	def fromPath(path):
		if os.path.isfile(path):
			return Config.fromFilePath(path)
		elif os.path.isdir(path):
			return Config.fromGitRepo(path)
		else:
			raise Exception("Can't read config from '%s'" % (path,))

	@staticmethod
	def fromGitRepo(repoPath):
		gC = git.Git(repoPath)

		if not 'gitdh' in gC.getBranches():
			raise Exception("No Branch 'gitdh' in repository '%s'" % (repoPath,))

		gFile = None
		for file in gC.getFiles(branch='gitdh'):
			if file.getFileName() == 'gitdh.conf':
				gFile = file
				break
		if gFile == None:
			raise Exception("No File 'gitdh.conf' in branch 'gitdh' in repository '%s'" % (repoPath,))

		config = Config()
		config.read_string(gFile.getFileContent())
		config.repoPath = repoPath
		return config

	@staticmethod
	def fromFilePath(filePath):
		with open(filePath) as f:
			config = Config.fromFile(f)

		return config

	@staticmethod
	def fromFile(fileObj):
		c = Config()
		c.read_file(fileObj)
		return c

	def __init__(self):
		super().__init__()
		self.branches = ConfigBranches(self)
		self._repoPath = None

	@property
	def repoPath(self):
		if self._repoPath == None:
			return self.get('Git', 'RepositoryPath', fallback=None)
		return self._repoPath

	@repoPath.setter
	def repoPath(self, repoPath):
		self._repoPath = repoPath


class ConfigBranches(Mapping):
	def __init__(self, cfgParser):
		self._cfgParser = cfgParser

	def keys(self):
		return (s for s in self._cfgParser if self._isBranchSection(s))

	def __len__(self):
		return len([i for i in self.keys()])

	def __contains__(self, item):
		return item in self.keys()

	def __iter__(self):
		return self.keys()

	def __getitem__(self, key):
		if not self._isBranchSection(key):
			raise KeyError("Invalid branch section '%s'" % (key,))
		return self._cfgParser[key]

	def _isBranchSection(self, key):
		# lazily load module config list
		return not key in ('Git', 'DEFAULT', 'Database') and not ("-" in key and key[key.rfind('-') + 1:] == "command")
