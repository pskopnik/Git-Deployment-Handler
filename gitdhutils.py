# -*- coding: utf-8 -*-

import os
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR

def deleteDirContent(dir):
	for file in os.listdir(dir):
		file_path = os.path.join(dir, file)
		try:
			if os.path.isdir(file_path):
				deleteDir(file_path)
			else:
				os.unlink(file_path)
		except Exception as e:
			print(e)

def deleteDir(dir):
	for file in os.listdir(dir):
		file_path = os.path.join(dir, file)
		try:
			if os.path.isdir(file_path):
				deleteDir(file_path)
			else:
				os.unlink(file_path)
		except Exception as e:
			print(e)
	try:
		os.rmdir(dir)
	except Exception as e:
		print(e)

def deleteUpdateRepo(path, repositoryname, branch, repositoriesDir, commit=None):
	path = path.rstrip("/ ")
	deleteDirContent(path)
	args = ('git', 'clone', '-q', '-l', '-s', '-b', branch, 'file://' + os.path.join(repositoriesDir, repositoryname + '.git'), os.path.basename(path))
	returncode = call(args, cwd=os.path.dirname(path), stdout=open('/dev/null'), stderr=open('/dev/null'))
	if returncode != 0:
		syslog(LOG_ERR, "Git return code after pulling is '{0}', branch '{1}'".format(returncode, branch))
	if not commit == None:
		args = ('git', 'checkout', commit)
		returncode = call(args, cwd=path, stdout=open('/dev/null'), stderr=open('/dev/null'))
		if returncode != 0:
			syslog(LOG_ERR, "Git return code after checkout of the commit '{0}' is '{1}', branch '{2}'".format(commit, returncode, branch))
		args = ('git', 'reset', '--hard', '-q')
		returncode = call(args, cwd=path, stdout=open('/dev/null'), stderr=open('/dev/null'))
		if returncode != 0:
			syslog(LOG_ERR, "Git return code after resetting to head is '{0}', branch '{1}'".format(returncode, branch))


def mInsertCommit(dbCon, commits):
	for commit in commits:
		insertCommit(dbCon, commit)


def insertCommit(dbCon, commit):
	if not hasattr(commit, "id") or commit.id == None:
		dbCon.insertCommit(commit)


def mInsertOnStatus(status, dbCon, commits):
	for commit in commits:
		insertOnStatus(status, dbCon, commit)


def insertOnStatus(status, dbCon, commit):
		if commit.status == status:
			insertCommit(dbCon, commit)


def filterOnStatusBase(statusBase, commits):
	filteredCommits = []
	for commit in commits:
		if '_' in commit.status and commit.status[:commit.status.rfind('_')] == statusBase:
			filteredCommits.append(commit)
	return filteredCommits


def filterOnStatusExt(statusExt, commits):
	filteredCommits = []
	for commit in commits:
		if '_' in commit.status and commit.status[commit.status.rfind('_') + 1:] == statusExt:
			filteredCommits.append(commit)
	return filteredCommits
