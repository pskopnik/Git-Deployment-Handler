import argh, os, sys
from gitdh.gitdh import gitDhMain
from gitdh.config import Config

try:
	from shlex import quote
except ImportError:
	import re
	_find_unsafe = re.compile(r'[^\w@%+=:,./-]', re.ASCII).search
	def quote(s):
		"""Return a shell-escaped version of the string *s*."""
		if not s:
			return "''"
		if _find_unsafe(s) is None:
			return s

		# use single quotes, and put single quotes into double quotes
		# the string $'b is then quoted as '$'"'"'b'
		return "'" + s.replace("'", "'\"'\"'") + "'"


postreceiveContent = """#!/bin/sh

configFile='{0}'
{1}
while read oldrev newrev refname
do
	git-dh postreceive $configFile $oldrev $newrev $refname
done

exit 0
"""

cronContent = """# {0}: Cron file for git-dh

PATH={1}
MAILTO={2}

{3}    {4}    {5}
"""


def cron(*target):
	for t in target:
		gitDhMain(t, 'cron', [])

def postreceive(target, oldrev, newrev, refname):
	gitDhMain(target, 'postreceive', [oldrev, newrev, refname])

@argh.named('postreceive')
@argh.arg('--printOnly', '--print', '-p')
@argh.arg('--force', '-f')
@argh.arg('--quiet', '-q')
@argh.arg('--mode')
def installPostreceive(printOnly=False, force=False, quiet=False, mode='755', *target):
	if force and printOnly:
		print("Invalid options: --printOnly and --force both set", file=sys.stderr)
		sys.exit(1)

	filesToWrite = {}
	virtEnvStr = ''
	if 'VIRTUAL_ENV' in os.environ:
		virtEnvStr = '. %s/bin/activate\n' % (quote(os.environ['VIRTUAL_ENV']),)
	for t in target:
		try:
			c = Config.fromFilePath(t)
			if c.repoPath is None:
				raise Exception("Missing RepositoryPath for '%s'" % (t))
			fPath = os.path.join(c.repoPath, 'hooks/post-receive')
			if not printOnly and not os.access(os.path.dirname(fPath), os.W_OK):
				raise Exception("Can't write to '%s'" % (fPath,))
			if not printOnly and os.path.exists(fPath) and not force:
				raise Exception("'%s' exists already, use --force to overwrite" % (fPath,))

			configFile = os.path.abspath(t)
			filesToWrite[fPath] = postreceiveContent.format(configFile, virtEnvStr)
		except Exception as e:
			print(e, file=sys.stderr)
			sys.exit(1)

	for (path, content) in filesToWrite.items():
		if printOnly:
			yield "# File '%s'" % path
			yield content
		else:
			try:
				if not quiet:
					yield "Writing post-receive hook '%s'" % (path,)
				with open(path, 'w') as f:
					f.write(content)
					# Only on UNIX
					#os.fchmod(f, mode)
				os.chmod(fPath, int(mode, 8))
			except (IOError, OSError) as e:
				print(e, file=sys.stderr)
				print("Please check '%s'" % (path,), file=sys.stderr)
				sys.exit(1)

@argh.named('cron')
@argh.arg('name', help="Name of the cron job file to be placed into /etc/cron.d")
@argh.arg('--user', '-u')
@argh.arg('--printOnly', '--print', '-p')
@argh.arg('--force', '-f')
@argh.arg('--quiet', '-q')
@argh.arg('--mailto')
@argh.arg('--unixPath', '--path')
@argh.arg('--interval', '-i')
def installCron(name, user=None, printOnly=False, force=False, quiet=False,
				mailto='root', unixPath=None, interval='*/5 * * * *', mode='644', *target):
	if force and printOnly:
		print("Invalid options: --printOnly and --force both set", file=sys.stderr)
		sys.exit(1)

	if user is None:
		user = os.getlogin()

	fPath = os.path.join('/etc/cron.d', name)
	try:
		for t in target:
			Config.fromPath(t)
		if not printOnly and not os.access(os.path.dirname(fPath), os.W_OK):
			raise Exception("Can't write to '%s'" % (fPath,))
		if not printOnly and os.path.exists(fPath) and not force:
			raise Exception("'%s' exists already, use --force to overwrite" % (fPath,))
	except Exception as e:
		print(e, file=sys.stderr)
		sys.exit(1)

	cmdStr = 'git-dh cron {0}'
	cmdOpts = ''
	first = True
	for t in target:
		if first:
			first = False
		else:
			cmdOpts += ' '
		cmdOpts += quote(os.path.abspath(t))
	cmdStr = cmdStr.format(cmdOpts)
	if 'VIRTUAL_ENV' in os.environ:
		virtEnvPath = os.path.join(os.environ['VIRTUAL_ENV'], 'bin', 'activate')
		cmdStr = ". %s; %s" % (quote(virtEnvPath), cmdStr)
		cmdStr = "bash -c %s" % (quote(cmdStr),)
	if unixPath == None:
		unixPath = os.environ.get('PATH', '')
	content = cronContent.format(fPath, unixPath, mailto, interval, user, cmdStr)

	if printOnly:
		yield "# File '%s'" % fPath
		yield content
	else:
		try:
			if not quiet:
				yield "Writing cron job '%s'" % (fPath,)
			with open(fPath, 'w') as f:
				f.write(content)
				# Only on UNIX
				#os.fchmod(f, mode)
			os.chmod(fPath, int(mode, 8))
		except (IOError, OSError) as e:
			print(e, file=sys.stderr)
			print("Please check '%s'" % (fPath,), file=sys.stderr)
			sys.exit(1)


parser = argh.ArghParser()
parser.add_commands([cron, postreceive])
parser.add_commands([installPostreceive, installCron], namespace="install")

if __name__ == '__main__':
	parser.dispatch()
