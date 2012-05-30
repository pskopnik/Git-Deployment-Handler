#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import databaseconnection
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteUpdateRepo, runPostprocessing

config = ConfigParser()
config.read("config.ini")
dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)

commits = dbCon.getAllAprovedCommits()
for commit in commits:
    dbCon.setStatusWorking(commit[0])
    if not config.has_section(commit[2]):
        syslog(LOG_ERR, "No section in the config for project '{0}' fetched with id '{1}'".format(commit[2],  commit[0]))
    else:
        path = config.get(commit[2], "StablePath")
        branch = commit[2] + "-stable"
        repositoryname = config.get(commit[2], "Repositoryname")
        syslog(LOG_INFO, "Pulling git for stable website '{0}'".format(commit[2]))
        deleteUpdateRepo(path,  repositoryname,  branch,  commit=commit[1])
        runPostprocessing(path, "stable", config, commit[2])
        dbCon.setStatusFinished(commit[0])
