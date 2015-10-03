# This script is used by py2exe to build distributable
# package with Win32 exe files not requiring python to run.
#
# this can be run with (you need to have py2exe installed):
# python setup.py py2exe
#
# Interesting note:
# http://www.py2exe.org/index.cgi/Py2exeAndPyQt

from setuptools import find_packages
from distutils.core import setup
import py2exe

print('Starting Py2exe version {0}'.format(py2exe.__version__))

# Win32 GUI, no console window
setup(
    name='xnovacmd',
    version='0.1',
    description='XNova browser game desktop client using Qt5',
    long_description='',
    url='https://github.com/minlexx/xnovacmd',
    author='Alexey Min',
    author_email='alexey.min@gmail.com',
    license='GPLv3',
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications :: Qt',

        # Indicate who your project is intended for
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment :: Turn Based Strategy',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing :: Markup :: HTML',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',

        'Natural Language :: English',
        'Natural Language :: Russian',

        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
    ],
    packages=find_packages(),
    install_requires=['requests', 'PyExecJS', 'PySocks', 'certifi'],
    # py2exe specific arguments
    console=['test_parser.py', 'test_requesocks.py', 'galaxy_auto_parser.py'],
    windows=[{
        "script": "app.py",
        "icon_resources": [(1, "ui/i/favicon.ico")]
    }],
    options={"py2exe": {"includes": ["sip"]}}
)
