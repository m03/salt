# -*- coding: utf-8 -*-
'''
    :synopsis: Unit Tests for Advanced Packaging Tool module 'module.aptpkg'
    :platform: Linux
    :maturity: develop
    versionadded:: nitrogen
'''

# Import Python Libs
from __future__ import absolute_import
import copy

# Import Salt Libs
from salt.exceptions import SaltInvocationError
from salt.modules import aptpkg

# Import Salt Testing Libs
from salttesting import TestCase, skipIf
from salttesting.helpers import ensure_in_syspath
from salttesting.mock import (
    MagicMock,
    patch,
    NO_MOCK,
    NO_MOCK_REASON,
)

ensure_in_syspath('../../')

# Globals
aptpkg.__salt__ = {}

APT_KEY_LIST = r'''
pub:-:1024:17:46181433FBB75451:1104433784:::-:::scSC:
fpr:::::::::C5986B4F1257FFA86632CBA746181433FBB75451:
uid:-::::1104433784::B4D41942D4B35FF44182C7F9D00C99AF27B93AD0::Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>:
'''

REPO_KEYS = {
    '46181433FBB75451': {
        'algorithm': 17,
        'bits': 1024,
        'capability': 'scSC',
        'date_creation': 1104433784,
        'date_expiration': None,
        'fingerprint': 'C5986B4F1257FFA86632CBA746181433FBB75451',
        'keyid': '46181433FBB75451',
        'uid': 'Ubuntu CD Image Automatic Signing Key <cdimage@ubuntu.com>',
        'uid_hash': 'B4D41942D4B35FF44182C7F9D00C99AF27B93AD0',
        'validity': '-'
    }
}

LOWPKG_FILES = {
    'errors': {},
    'packages': {
        'wget': [
            '/.',
            '/etc',
            '/etc/wgetrc',
            '/usr',
            '/usr/bin',
            '/usr/bin/wget',
            '/usr/share',
            '/usr/share/info',
            '/usr/share/info/wget.info.gz',
            '/usr/share/doc',
            '/usr/share/doc/wget',
            '/usr/share/doc/wget/MAILING-LIST',
            '/usr/share/doc/wget/NEWS.gz',
            '/usr/share/doc/wget/AUTHORS',
            '/usr/share/doc/wget/copyright',
            '/usr/share/doc/wget/changelog.Debian.gz',
            '/usr/share/doc/wget/README',
            '/usr/share/man',
            '/usr/share/man/man1',
            '/usr/share/man/man1/wget.1.gz',
        ]
    }
}

LOWPKG_INFO = {
    'wget': {
        'architecture': 'amd64',
        'description': 'retrieves files from the web',
        'homepage': 'http://www.gnu.org/software/wget/',
        'install_date': '2016-08-30T22:20:15Z',
        'maintainer': 'Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>',
        'name': 'wget',
        'section': 'web',
        'source': 'wget',
        'version': '1.15-1ubuntu1.14.04.2'
    }
}

APT_Q_UPDATE = '''
Get:1 http://security.ubuntu.com trusty-security InRelease [65 kB]
Get:2 http://security.ubuntu.com trusty-security/main Sources [120 kB]
Get:3 http://security.ubuntu.com trusty-security/main amd64 Packages [548 kB]
Get:4 http://security.ubuntu.com trusty-security/main i386 Packages [507 kB]
Hit http://security.ubuntu.com trusty-security/main Translation-en
Fetched 1240 kB in 10s (124 kB/s)
Reading package lists...
'''


@skipIf(NO_MOCK, NO_MOCK_REASON)
class AptPkgTestCase(TestCase):
    '''
    Test cases for salt.modules.aptpkg
    '''

    def test_version(self):
        '''
        Test - Returns a string representing the package version or an empty string if
        not installed.
        '''
        version = LOWPKG_INFO['wget']['version']
        mock = MagicMock(return_value=version)
        with patch.dict(aptpkg.__salt__, {'pkg_resource.version': mock}):
            self.assertEqual(aptpkg.version(*['wget']), version)

    @patch('salt.modules.aptpkg.latest_version',
           MagicMock(return_value=''))
    def test_upgrade_available(self):
        '''
        Test - Check whether or not an upgrade is available for a given package.
        '''
        self.assertFalse(aptpkg.upgrade_available('wget'))

    @patch('salt.modules.aptpkg.get_repo_keys',
           MagicMock(return_value=REPO_KEYS))
    def test_add_repo_key(self):
        '''
        Test - Add a repo key.
        '''
        mock = MagicMock(return_value={
            'retcode': 0,
            'stdout': 'OK'
        })
        with patch.dict(aptpkg.__salt__, {'cmd.run_all': mock}):
            self.assertTrue(aptpkg.add_repo_key(keyserver='keyserver.ubuntu.com',
                                                keyid='FBB75451'))

    @patch('salt.modules.aptpkg.get_repo_keys',
           MagicMock(return_value=REPO_KEYS))
    def test_add_repo_key_failed(self):
        '''
        Test - Add a repo key using incomplete input data.
        '''
        kwargs = {'keyserver': 'keyserver.ubuntu.com'}
        mock = MagicMock(return_value={
            'retcode': 0,
            'stdout': 'OK'
        })
        with patch.dict(aptpkg.__salt__, {'cmd.run_all': mock}):
            self.assertRaises(SaltInvocationError, aptpkg.add_repo_key, **kwargs)

    def test_get_repo_keys(self):
        '''
        Test - List known repo key details.
        '''
        mock = MagicMock(return_value={
            'retcode': 0,
            'stdout': APT_KEY_LIST
        })
        with patch.dict(aptpkg.__salt__, {'cmd.run_all': mock}):
            self.assertEqual(aptpkg.get_repo_keys(), REPO_KEYS)

    def test_file_dict(self):
        '''
        Test - List the files that belong to a package, grouped by package.
        '''
        mock = MagicMock(return_value=LOWPKG_FILES)
        with patch.dict(aptpkg.__salt__, {'lowpkg.file_dict': mock}):
            self.assertEqual(aptpkg.file_dict('wget'), LOWPKG_FILES)

    def test_file_list(self):
        '''
        Test - List the files that belong to a package.
        '''
        files = {
            'errors': LOWPKG_FILES['errors'],
            'files': LOWPKG_FILES['packages']['wget'],
        }
        mock = MagicMock(return_value=files)
        with patch.dict(aptpkg.__salt__, {'lowpkg.file_list': mock}):
            self.assertEqual(aptpkg.file_list('wget'), files)

    def test_get_selections(self):
        '''
        Test - View package state from the dpkg database.
        '''
        selections = {'install': ['wget']}
        mock = MagicMock(return_value='wget\t\t\t\t\t\tinstall')
        with patch.dict(aptpkg.__salt__, {'cmd.run_stdout': mock}):
            self.assertEqual(aptpkg.get_selections('wget'), selections)

    def test_info_installed(self):
        '''
        Test - Return the information of the named package(s) installed on the system.
        '''
        names = {
            'group': 'section',
            'packager': 'maintainer',
            'url': 'homepage'
        }

        installed = copy.deepcopy(LOWPKG_INFO)
        for name in names:
            if installed['wget'].get(names[name], False):
                installed['wget'][name] = installed['wget'].pop(names[name])

        mock = MagicMock(return_value=LOWPKG_INFO)
        with patch.dict(aptpkg.__salt__, {'lowpkg.info': mock}):
            self.assertEqual(aptpkg.info_installed('wget'), installed)

    def test_owner(self):
        '''
        Test - Return the name of the package that owns the file.
        '''
        paths = ['/usr/bin/wget']
        mock = MagicMock(return_value='wget: /usr/bin/wget')
        with patch.dict(aptpkg.__salt__, {'cmd.run_stdout': mock}):
            self.assertEqual(aptpkg.owner(*paths), 'wget')

    def test_refresh_db(self):
        '''
        Test - Updates the APT database to latest packages based upon repositories.
        '''
        refresh_db = {
            'http://security.ubuntu.com trusty-security InRelease': True,
            'http://security.ubuntu.com trusty-security/main Sources': True,
            'http://security.ubuntu.com trusty-security/main Translation-en': None,
            'http://security.ubuntu.com trusty-security/main amd64 Packages': True,
            'http://security.ubuntu.com trusty-security/main i386 Packages': True
        }
        mock = MagicMock(return_value={
            'retcode': 0,
            'stdout': APT_Q_UPDATE
        })
        with patch.dict(aptpkg.__salt__, {'cmd.run_all': mock}):
            self.assertEqual(aptpkg.refresh_db(), refresh_db)

if __name__ == '__main__':
    from integration import run_tests  # pylint: disable=import-error
    run_tests(AptPkgTestCase, needs_daemon=False)
