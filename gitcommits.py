#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, git, shlex, re
from subprocess import call, CalledProcessError
from syslog import syslog, LOG_ERR
from configparser import ConfigParser

def deleteDirContent(dir):
    for the_file in os.listdir(dir):
        file_path = os.path.join(dir, the_file)
        try:
            if os.path.isdir(file_path):
                deleteDir(file_path)
            else:
                os.unlink(file_path)
        except Exception as e:
            print(e)

def deleteDir(dir):
    for the_file in os.listdir(dir):
        file_path = os.path.join(dir, the_file)
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

def getAllFiles(path):
    allFiles = list()
    pathcontent = os.walk(path)
    for root, dirs, files in pathcontent:
        for file in files:
            allFiles.append(os.path.join(root, file))
    return allFiles

def filterFiles(files, regexp):
    filteredFiles = list()
    regexp = re.compile(regexp)
    for file in files:
        if not regexp.search(file) == None:
            filteredFiles.append(file)
    return filteredFiles

def executePathCommand(command, path, basepath):
    command = command.replace("${f}", "'" + path + "'")
    args = shlex.split(command)
    return call(args, stdout=open('/dev/null'), stderr=open('/dev/null'), cwd=basepath)

def runPostprocessing(path, config, sectionname):
    if config.has_option(sectionname, "Postprocessing"):
        postprocCommandString = config.get(sectionname, "Postprocessing")
        postprocCommands = postprocCommandString.split(" ")
        for postprocCommand in postprocCommands:
            if not config.has_section(postprocCommand + "-command"):
                syslog(LOG_ERR, "Command '{0}' doesn't exist".format(postprocCommand))
            else:
                configMode = config.get(postprocCommand + "-command", "Mode")
                if configMode == "once":
                    executePathCommand(config.get(postprocCommand + "-command", "Command"), path, path)
                elif configMode == "perfile":
                    files = getAllFiles(path)
                    if config.has_option(postprocCommand + "-command", "RegExp"):
                        files = filterFiles(files, config.get(postprocCommand + "-command", "RegExp"))
                    for file in files:
                        executePathCommand(config.get(postprocCommand + "-command", "Command"), file, path)

def getAndInsertCommits(config, branch, firstcommit, lastcommit, dbCon, status=1):
    gC = git.Git(config.get(branch, "Repositoryname"), repositoriesDir=config.get("Git", "RepositoriesDir"))
    commits = gC.getLog(firstcommit, lastcommit)
    for commit in commits:
        commitMessage = commit.getMessage()
        if len(commitMessage) > 300:
            commitMessage = commitMessage[:297] + "..."
        dbCon.insertCommit(commit.getHash(), commit.getAuthor() , commit.getDate(), commitMessage, config.get(branch, "Repositoryname"), branch, status)