# -*- coding: utf-8 -*-

from gitdh.modules import Module
from syslog import syslog, LOG_INFO, LOG_WARNING
from gitdh.gitdhutils import filterOnStatusExt, deleteDir, deleteDirContent
import os
from os.path import abspath, join, exists, isdir, isfile
from subprocess import check_call, CalledProcessError

class Deployment(Module):
	def isEnabled(self, action):
		return True

	def filter(self, commits):
		commits = filterOnStatusExt('queued', commits)
		branches = {}
		for commit in commits:
			if not commit.branch in branches:
				branches[commit.branch] = []
			branches[commit.branch].append(commit)

		for branch in branches.values():
			sortedCommits = sorted(branch, key=lambda commit: commit.date)
			for commit in sortedCommits[:-1]:
				self._removeCommit(commit)

	def processRemoved(self, commits):
		if not self.dbBe is None:
			for commit in commits:
				if commit.removers == [self]:
					self.dbBe.setStatusSkipped(commit)

	def process(self, commits):
		commits = filterOnStatusExt('queued', commits)
		for commit in commits:
			if not self.dbBe is None:
				self.dbBe.setStatusWorking(commit)

			confSection = self.config.branches[commit.branch]
			rmIntGitFiles = confSection.getboolean('RmIntGitFiles', True)
			if not hasattr(commit, 'deploymentSource'):
				commit.deploymentSource = self.config.repoPath
			syslog(LOG_INFO, "Deploying commit '%s' from '%s' : '%s' to '%s'" % (commit, commit.repository, commit.branch, confSection['Path']))

			self._deleteUpdateRepo(confSection['Path'], commit.deploymentSource, commit.branch, commit, rmIntGitFiles=rmIntGitFiles)

			if not self.dbBe is None:
				self.dbBe.setStatusFinished(commit)

	def _deleteUpdateRepo(self, path, sourceRepository, branch, commit, rmIntGitFiles=True):
		path = abspath(path)
		try:
			if not exists(path):
				os.mkdir(path)
			else:
				if not isdir(path):
					syslog(LOG_WARNING, "Not a directory '%s'" % (path,))
					return
				deleteDirContent(path)
		except OSError as e:
			syslog(LOG_WARNING, "OSError while clearing '%s': '%s'" % (path, e))
			return

		if exists(sourceRepository):
			args = ('git', 'clone', '-q', '-l', '-s', '-b', branch, 'file://' + sourceRepository, path)
		else:
			args = ('git', 'clone', '-q', '-b', branch, sourceRepository, path)

		with open(os.devnull, 'w') as devNull:
			try:
				check_call(args, cwd=path, stdout=devNull, stderr=devNull)
				if not commit is None:
					args = ('git', 'checkout', commit.hash)
					check_call(args, cwd=path, stdout=devNull, stderr=devNull)
					args = ('git', 'reset', '--hard', '-q')
					check_call(args, cwd=path, stdout=devNull, stderr=devNull)
				if rmIntGitFiles:
					self._rmIntGitFiles(path)
			except CalledProcessError as e:
				syslog(LOG_WARNING, "Git Error: '%s'" % (e,))

	def _rmIntGitFiles(self, path):
			deleteDir(join(path, '.git'))
			if isfile(join(path, '.gitignore')):
				os.unlink(join(path, '.gitignore'))
