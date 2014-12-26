Git Deployment Handler
======================

The Git Deployment Handler is a tool for automatic deployment of git
commits from local or remote repositories into directories.

Some advanced features require a database; SQlite, MongoDb and MySQL are
the supported database backends. The Git Deployment Handler uses
post-receive hooks and cron jobs (services in future) to automatically
deploy commits.

Requirements
------------

-  python3
-  git (command line tool)
-  **For some features either**

   -  *sqlite3*
   -  mysql and PyMySQL
   -  mongodb and pymongo

Installation
------------

The easiest way to install
`gitdh <https://pypi.python.org/pypi/gitdh/>`__ is to use the `Python
Package Index <https://pypi.python.org/pypi>`__:

::

    # pip install gitdh

Or manually install from source:

::

    # python3 setup.py install

Configuration
-------------

gitdh is configured using a config file in INI syntax.

It can either be stored somewhere on the file system or in a file named
``gitdh.conf`` in a ``gitdh`` branch of a git repository. This file or
such a git repository is referred to as **target** within gitdh. Some
sample config files can be found in the ``docs/`` directory.

The ``Git`` section of the file contains all file-wide settings; The
most important one is the ``RepositoryPath`` of the git repository to be
deployed. This setting can be omitted when the config file is placed in
a git repository (named ``gitdh.conf`` in a ``gitdh`` branch).

::

    [Git]
    RepositoryPath = /var/lib/gitolite/repositories/webapp.git

Additional Options:

-  ``External`` - ``True`` or ``False``, whether the Source is an
   external (i.e. remote) repository (requires a database); default
   ``False``
-  ``IdentityFile`` - May contain the path of an IdentityFile (as in
   .ssh/config) when External is used and Source is a SSH URL; default
   ``None``

Branches
~~~~~~~~

For every branch which should be deployed, a section named like the
branch has to be created. The ``Path`` setting specifies the path to be
deployed to:

::

    [master]
    Path = /srv/www/webapp.com/

Additional Options:

-  ``RmGitIntFiles`` - ``True`` or ``False``, whether internal git files
   should be deleted (``.git/``, ``.gitignore``, ``.gitmodules``);
   default ``True``
-  ``Recursive`` - ``True`` or ``False``, whether a clone should be
   ``recursive``, i.e. submodules should be cloned out as well; default
   ``True``
-  ``DatabaseLog`` - ``True`` or ``False``, whether every commit should
   be logged to the database; default ``False``
-  ``CronDeployment`` - ``True`` or ``False``, whether every commit
   should be inserted into the database and deployed by cron job instead
   of being deploying directly; default ``False``
-  ``Approval`` - ``True`` or ``False``, whether every commit has to be
   first approved in the database and is then deployed by cron job;
   default ``False``
-  ``Preprocessing`` - space separated list of commands to be performed
   before deploying any commits; default \`\` (empty)
-  ``Postprocessing`` - space separated list of commands to be performed
   after deploying all commits; default \`\` (empty)

Database
~~~~~~~~

To be able to utilise a database, a ``Database`` section is required.
The ``Engine`` setting in the ``Database`` section specified the
database backend (must be ``sqlite``, ``mongodb`` or ``mysql``). Each
database backend has its own further options:

::

    # MySQL
    # Database and table have to be setup, see docs/commits.sql
    [Database]
    Engine = mysql
    Host = localhost
    Port = 3306
    User = gitdh
    Password = ###randompassword###
    Database = gitdh
    Table = commits

    # MongoDb
    # Database and collection are created when needed
    [Database]
    Engine = mongodb
    Host = localhost
    Port = 27017
    Database = git-commits
    Collection = commits

    # SQLite
    # Is created when needed; DatabaseFile must be writable
    [Database]
    Engine = sqlite
    DatabaseFile = /var/lib/gitolite/data.sqlite
    Table = commits

Commands
~~~~~~~~

Commands used for ``Preprocessing`` and ``Postprocessing`` are stored in
additional sections in the config file. The section name is the name of
the command with trailing ``-command``.

::

    [crunch-command]
    Mode = file
    RegExp = \.php$
    Command = eff_php_crunch ${f}

    [customscript-command]
    Mode = once
    Command = ${f}/custom.sh

``Mode`` can either be ``file`` or ``once``. The ``Command`` defines the
command which is executed. In the ``Command`` string ``${f}`` is
substituted with a file path:

-  If ``Mode`` equals ``file``, the command is performed once for every
   file in the repository matching the regular expression in the
   optional ``RegExp`` option. The file path is the path of the
   individual file in this case.
-  If ``Mode`` equals ``once``, the command is performed once for the
   deployed repository, the file path in this case is the path of the
   deployed repository.

Additional Options:

-  ``Shell`` - ``True`` or ``False``, whether a shell should be used to
   execute the command; default ``False``
-  ``SuppressOutput`` - ``True`` or ``False``, whether output from the
   command should be surpressed, whether ; default ``True``

Setup
-----

In order to deploy commits automatically, gitdh has to be installed as a
git post-receive hook and / or a cron job. Post-receive hooks require a
local "git server" (e.g. `gitolite <http://gitolite.com/>`__) commits
are pushed to. Cron Jobs have to be created to use advanced features,
e.g. deploy commits from ``External`` repositories or the ``Approval``
or ``CronDeployment`` features.

The ``git-dh install`` command helps creating these files.

``postreceive`` Setup
~~~~~~~~~~~~~~~~~~~~~

The ``git-dh install postreceive`` command will assist on creating git
post-receive hooks.

The following command will attempt to create a post-receive hook for
every ``target`` (being a config file or a repository):

::

    # git-dh install postreceive <target>[ <target>[ <target> ...]]

The command will try to fetch all required information from the
``target``. It will also attempt to recognise and use the current
virtualenv. The command by default doesn't overwrite any files, aborts
on error and prints all files written to.

Additional arguments:

-  ``--printOnly`` - Only print the file content, don't write any files
-  ``--force`` - Overwrite existing files
-  ``--quiet`` - Only print errors
-  ``--mode`` - The mode of the created file; default 755

For more information see ``git-dh install postreceive --help``.

A sample post-receive file can be found in ``docs/post-receive.sample``

``cron`` Setup
~~~~~~~~~~~~~~

The ``git-dh install cron`` command will assist on creating cron job
files in ``/etc/cron.d/``.

The following command will attempt to create a cron job ``name`` in
``/etc/cron.d/`` containing commands to query every ``target`` (being a
config file or a repository):

::

    # git-dh install cron <name> <target>[ <target>[ <target> ...]]

The command will try to fetch all required information from the
``target``. It will also attempt to recognise and use the current
virtualenv. The command by default doesn't overwrite any files, aborts
on error and prints all files written to.

Additional arguments:

-  ``--user`` - The user to execute gitdh under; default: the current
   user
-  ``--interval`` - The interval with which the cron job is to be
   executed; default ``*/5 * * * *``
-  ``--unixPath`` - The ``PATH`` to be written to the cron job file;
   default: the current path
-  ``--printOnly`` - Only print the file content, don't write any files
-  ``--force`` - Overwrite existing files
-  ``--quiet`` - Only print errors
-  ``--mode`` - The mode of the created file; default 644

For more information see ``git-dh install cron --help``.

A sample cron job file can be found in ``docs/cronjob.sample``

Issues / Contributing
---------------------

Please use the `Git-Deployment-Handler Github
Repository <https://github.com/seoester/Git-Deployment-Handler>`__ to
submit issues or contribute.
