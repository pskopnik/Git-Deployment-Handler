Git Deployment Handler
======================

The Git Deployment Handler is a tool to manage the deployment of
git branches into directories. An approval system is built in,
MongoDb and MySQL (sqlite will be added soon) are the supported
DatabaseBackends. It uses the git post-receive hook and a cron job
(only needed for the approval system) to automatically deploy
commits.

Requirements
------------


-  python3.2
-  *Either*
-  mysql and PyMySQL
-  mongodb and pymongo

Installation
------------

The easiest way to install gitdh is to use the Python Package Index
(available tomorrow):

::

    # pip install gitdh

Of course a manual installation is possible as well:

::

    # python3 setup.py install

Configuration
-------------

gitdh is configured using a config file in INI syntax. It can
either be stored somewhere on the local file system or in a file
named ``gitdh.conf`` in a ``gitdh`` branch in the git repository
the ``post-receive`` hook is installed in (see the
*post-receive setup* section). A complete example config file can
be found in docs/gitdh.conf.sample.

Necessary sections of the config file are ``Database`` and ``Git``

::

    # Database must either be mysql or mongodb
    
    # The structure for the necessary `commits` table can be found in docs/commits.sql
    [Database]
    Engine = mysql
    Host = localhost
    Port = 3306
    User = root
    Password = root
    Database = git-commits
    Table = commits
    
    # MongoDb requires no structure or preconfiguration
    [Database]
    Engine = mongodb
    Host = localhost
    Port = 27017
    Database = git-commits
    Collection = commits
    
    # Git has to contain the path of the folder where the bare git repositories are stored in
    # Additionally it can contain the name of the repository which should be exported, when the option
    # is set, the given value is the default for the whole file.
    # If only the 'postreceive' action is used for a repository, both options can be set to 'AUTO'.
    [Git]
    RepositoriesDir = /var/lib/gitolite/repositories/
    #RepositoryName = website

For every branch which should be deployed by gitdh a new section
has to be created.

::

    # The master is branch is being deployed.
    [master]
    # Deploy to /var/www_dev
    Path = /var/www_dev/
    RepositoryName = website

Other options are:


-  ``DatabaseLog`` - ``True`` or ``False``, whether every commit
   should be logged to the database
-  ``CronDeployment`` - ``True`` or ``False``, whether every commit
   should be inserted into the database and deployed by cron job
   instead of deploying it directly, e.g. when permissions aren't
   available
-  ``Approval`` - ``True`` or ``False``, whether every commit has
   to be first approved in the database and is then deployed by cron
   job
-  ``Postprocessing`` - space separated list of commands which
   should be performed onto the deployed files

Commands
~~~~~~~~

Commands are stored in additional sections in the config file. The
section name is the name of the command with trailing
``-command``.

::

    [crunch-command]
    Mode = perfile
    RegExp = \.php$
    Command = eff_php_crunch ${f}
    
    [customscript-command]
    Mode = once
    Command = ${f}/custom.sh

``Mode`` can either be ``perfile`` or ``once``. The command defines
the actual command which is executed. In the Command string
``${f}`` is substituted with a file path.

If ``Mode`` equals ``perfile``, the command is performed once for
every file in the repository which matches the regular expression
in the optional ``RegExp`` option. The file path is the path of the
individual file in this case.

If ``Mode`` equals ``once``, the command is performed once for the
deployed repository, the file path in this case is the path of the
deployed repository.

``postreceive`` Setup
---------------------

The post-receive hook can be set up automatically with the
``git-dh-pr`` command:

::

    # cd /var/lib/gitolite/repositories/website.git/hooks
    # git-dh-pr --install

After the setup with ``git-dh-pr`` the ``gitdh.conf`` file in the
``gitdh`` branch is automatically used as the configuration file.
*Unfortunately this setup doesn't support cron *yet*, please check tomorrow again.*

A static setup still can be used, see docs/post-receive.static for
an example.

``cron`` Setup
--------------

To perform cron database checks, the ``git-dh`` has to be called
with the ``cron`` action.

::

    git-dh <configfile> cron

To automate this, a cron file can be created in ``/etc/cron.d/``
(path for most linux distributions). An example file performing
``git-dh`` every five minutes can be found in docs/gitdh.cron


