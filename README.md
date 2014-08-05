Git Deployment Handler
=======================

The Git Deployment Handler is a tool to manage the deployment of git branches into directories.
An approval system is built in, MongoDb, MySQL and sqlite are the supported DatabaseBackends.
It uses the git post-receive hook and a cron job (only needed for Approval/DatabaseLog/CronDeployment/External) to automatically deploy commits.

##Requirements

 * python3.2
 * git (command line tool)
 * __For Approval/DatabaseLog/CronDeployment/External Either__
    * _sqlite3_
    * mysql and PyMySQL
    * mongodb and pymongo

##Installation

The easiest way to install gitdh is to use the Python Package Index:

    # pip install gitdh

Of course a manual installation is possible as well:

    # python3 setup.py install

##Configuration

gitdh is configured using a config file in INI syntax.
It can either be stored somewhere on the local file system or in a file named `gitdh.conf` in a `gitdh` branch in the git repository the `post-receive` hook is installed in (see the _post-receive setup_ section).
A complete example config file can be found in docs/gitdh.conf.sample.

Often a `Database` section is needed.

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

    # The databasefile has to be writable for all users git-dh is executed as
    [Database]
    Engine = sqlite
    DatabaseFile = /var/lib/gitolite/data.sqlite
    Table = commits

The `Git` section can contain default values for all branch sections in the config file.

    # Git can contain the path of the folder where the bare git repositories are stored in.
    # Additionally it can contain the name of the repository which should be exported, when the option
    # is set, the given value is the default for the whole file.
    # If only the `git-dh-pr` and `git-dh-cron` commands used for a repository, both options can be set to 'AUTO'.
    [Git]
    RepositoriesDir = /var/lib/gitolite/repositories/
    #RepositoryName = website

For every branch which should be deployed by gitdh a new section has to be created. The name of the section has to be the name of the branch which is deployed.

    # The master is branch is being deployed.
    [master]
    # Deploy to /var/www_dev
    Path = /var/www_dev/
    # The source repository, can be omitted when RepositoriesDir and RepositoryName are set in the Git section
    # or RepositoriesDir is set in the Git section and RepositoryName in the branch section
    #Source = /var/lib/gitolite/repositories/website.git
    # RepositoryName can be omitted when set in the Git section
    RepositoryName = website

The other available options are:

 * `DatabaseLog` - `True` or `False`, whether every commit should be logged to the database; default `False`
 * `CronDeployment` - `True` or `False`, whether every commit should be inserted into the database and deployed by cron job instead of deploying it directly, e.g. when permissions aren't available; default `False`
 * `Approval` - `True` or `False`, whether every commit has to be first approved in the database and is then deployed by cron job; default `False`
 * `Postprocessing` - space separated list of commands which should be performed onto the deployed files
 * `Preprocessing` - space separated list of commands which should be performed before deploying any commits
 * `RmGitIntFiles` - `True` or `False`, whether internal git files should be deleted (.git/ and .gitignore); default `True`
 * `External` - `True` or `False`, whether the Source is an external repository (only `cron` action); default `False`
 * `IdentityFile` - Can contain the path of an IdentityFile (as in .ssh/config) when External is used and Source is a SSH URL; default None

###Commands

Commands are stored in additional sections in the config file.
The section name is the name of the command with trailing `-command`.

    [crunch-command]
    Mode = perfile
    RegExp = \.php$
    Command = eff_php_crunch ${f}

    [customscript-command]
    Mode = once
    Command = ${f}/custom.sh

`Mode` can either be `perfile` or `once`. The command defines the actual command which is executed.
In the Command string `${f}` is substituted with a file path.

If `Mode` equals `perfile`, the command is performed once for every file in the repository which matches the regular expression in the optional `RegExp` option. The file path is the path of the individual file in this case.

If `Mode` equals `once`, the command is performed once for the deployed repository, the file path in this case is the path of the deployed repository.

##`postreceive` Setup

The post-receive hook can be set up automatically with the `git-dh-pr` command:

    # cd /var/lib/gitolite/repositories/website.git/hooks
    # git-dh-pr --install

After the setup with `git-dh-pr` the `gitdh.conf` file in the `gitdh` branch is automatically used as the configuration file. The `git-dh-pr` command can also create the post-receive hook in another directory and with another name:

    # git-dh-pr --install --name hooks/post-receive.gitdh

A static setup still can be used, see docs/post-receive.static as an example. A file like docs/post-receive.static has to be created with the name `post-receive` in the hooks/ directory of the git repository.

##`cron` Setup

To perform cron database checks, the `git-dh` has to be called with the `cron` action.

    git-dh <configfile> cron

If the setup is stored in a `gitdh.conf` file in the `gitdh` branch of an repository the `git-dh-cron` command has to be used.

    git-dh-cron <repository directory>...

To automate this, a cron file can be created in `/etc/cron.d/` (path for most linux distributions).
An example file performing `git-dh`/`git-dh-cron` every five minutes can be found in docs/gitdh.cron
