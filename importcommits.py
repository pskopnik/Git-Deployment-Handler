#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import git, sys, databaseconnection
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteUpdateRepo, runPostprocessing

config = ConfigParser()
config.read("config.ini")

project = sys.argv[1]
firstcommit = sys.argv[2]
lastcommit = sys.argv[3]
ref = sys.argv[4]

if not config.has_section(project):
    syslog(LOG_ERR, "No section in config for project '{0}'".format(project))
    exit(1)

if ref.find("refs/heads/") == 0:
    branch = ref[11:]
else:
    syslog(LOG_ERR,  "Branch name could not be parsed in '{0}'".format(ref))
    exit(1)

if branch == project + "-stable":
    syslog(LOG_INFO, "Inserting in the database for the stable website '{0}'".format(project))
    dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)
    
    gC = git.Git(config.get(project, "Repositoryname"))
    commits = gC.getLog(firstcommit, lastcommit)
    for commit in commits:
        commitMessage = commit.getMessage()
        if len(commitMessage) > 300:
            commitMessage = commitMessage[:297] + "..."
        
        dbCon.insertCommit(commit.getHash(), commit.getAuthor() , commit.getDate(), commitMessage, project)
    
elif branch == project+ "-dev":
    syslog(LOG_INFO, "Pulling git for dev website '{0}'".format(project))
    deleteUpdateRepo(config.get(project, "DevPath"), config.get(project, "Repositoryname"), project + "-dev")
    runPostprocessing(config.get(project, "DevPath"), "dev", config, project)
