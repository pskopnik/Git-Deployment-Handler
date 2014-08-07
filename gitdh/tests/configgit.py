import unittest, tempfile, os.path
from gitdh.config import Config
from gitdh.git import Git
from subprocess import check_output

class GitdhConfigGitTestCase(unittest.TestCase):

	def setUp(self):
		self.cStr = """
[Git]
RepositoryPath = /var/lib/gitolite/repositories/test.git

[Database]
Engine = sqlite
DatabaseFile = /var/lib/gitolite/data.sqlite
Table = commits

[master]
Path=/home/www/production

[development]
Path=/home/www/development

[crunch-command]
Mode = perfile
RegExp = \.php$
Command = eff_php_crunch ${f}
"""

	def test_gitRepo(self):
		d = tempfile.TemporaryDirectory()
		self._createGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		d.cleanup()

	def test_bareGitRepo(self):
		d = tempfile.TemporaryDirectory()
		self._createBareGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')
		self.assertEqual(c.repoPath, d.name)

		d.cleanup()

	def _createGitRepo(self, path):
		check_output(('git', 'init'), cwd=path)

		gC = Git(path)
		gC._executeGitCommand('config', 'user.email test@localhost')
		gC._executeGitCommand('config', 'user.name Test')

		with open(os.path.join(path, 'README'), 'w') as f:
			f.write('On master')
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Initial Import"')
		gC._executeGitCommand('branch', 'development')
		gC._executeGitCommand('checkout', 'development', suppressStderr=True)
		with open(os.path.join(path, 'README'), 'w') as f:
			f.write('On development')
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Development branch added"')

		gC._executeGitCommand('branch', 'gitdh')
		gC._executeGitCommand('checkout', 'gitdh', suppressStderr=True)
		with open(os.path.join(path, 'gitdh.conf'), 'w') as f:
			f.write(self.cStr)
		gC._executeGitCommand('add', '.')
		gC._executeGitCommand('commit', '-m "Gitdh conf added"')

		return gC

	def _createBareGitRepo(self, path):
		d = tempfile.TemporaryDirectory()
		self._createGitRepo(d.name)

		check_output(('git', 'clone', '--bare', d.name, path))

		d.cleanup()


