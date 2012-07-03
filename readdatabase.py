#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, databaseconnection
from syslog import syslog, LOG_ERR, LOG_INFO
from configparser import ConfigParser
from gitcommits import deleteUpdateRepo, runPostprocessing

configFile = "config.ini"
if len(sys.argv) > 1:
    configFile = sys.argv[1]

config = ConfigParser()
config.read(configFile)
dbCon = databaseconnection.DatabaseConnection.getDatabaseConnection(config=config)

commits = dbCon.getAllAprovedCommits()
for commit in commits:
    dbCon.setStatusWorking(commit[0], commit[3])
    if not config.has_section(commit[2]):
        syslog(LOG_ERR, "No section in the config for branch '{0}' fetched with id '{1}'".format(commit[2],  commit[0]))
    else:
        path = config.get(commit[2], "Path")
        repositoryname = config.get(commit[2], "Repositoryname")
        syslog(LOG_INFO, "Pulling git for branch '{0}'".format(commit[2]))
        deleteUpdateRepo(path, repositoryname, commit[2], config.get("Git", "RepositoriesDir"), commit=commit[1])
        runPostprocessing(path, config, commit[2])
        dbCon.setStatusFinished(commit[0], commit[3])
