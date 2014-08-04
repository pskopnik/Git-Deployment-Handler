import unittest, tempfile, os.path
from gitdh.config import Config, ConfigBranches
from gitdh.git import Git
from configparser import SectionProxy
from subprocess import check_output

class GitdhConfigTestCase(unittest.TestCase):

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
"""

	def test_branches(self):
		c = Config()
		c.read_string(self.cStr)

		self.assertTrue(isinstance(c.branches, ConfigBranches))

		self.assertEqual(len(c.branches), 2)

		self.assertFalse('feature-xyz' in c.branches)
		self.assertFalse('Git' in c.branches)
		self.assertFalse('Database' in c.branches)
		self.assertFalse('DEFAULT' in c.branches)
		self.assertTrue('development' in c.branches)
		self.assertTrue('master' in c.branches)

		self.assertRaises(KeyError, lambda: c.branches['feature-xyz'])
		self.assertRaises(KeyError, lambda: c.branches['Git'])
		self.assertRaises(KeyError, lambda: c.branches['Database'])
		self.assertRaises(KeyError, lambda: c.branches['DEFAULT'])

		self.assertSetEqual(set((i for i in c.branches)), set(('development', 'master')))

		self.assertTrue(isinstance(c.branches['development'], SectionProxy))
		self.assertTrue('Path' in c.branches['development'])
		self.assertFalse('External' in c.branches['development'])
		c['development']['External'] = 'False'
		self.assertTrue('External' in c.branches['development'])

	def test_file(self):
		f = tempfile.TemporaryFile(mode='w+')
		f.write(self.cStr)
		f.flush()
		f.seek(0)
		c = Config.fromFile(f)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		f.close()

	def test_filePath(self):
		f = tempfile.NamedTemporaryFile()
		f.write(self.cStr.encode())
		f.flush()
		c = Config.fromFilePath(f.name)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		c = Config.fromPath(f.name)

		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		f.close()

	def test_gitRepo(self):
		d = tempfile.TemporaryDirectory()
		self._createGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		d.cleanup()

	def test_bareGitRepo(self):
		d = tempfile.TemporaryDirectory()
		self._createBareGitRepo(d.name)

		c = Config.fromGitRepo(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

		c = Config.fromPath(d.name)
		self.assertTrue('Database' in c)
		self.assertTrue('master' in c)
		self.assertEqual(c['Database']['Engine'], 'sqlite')

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


