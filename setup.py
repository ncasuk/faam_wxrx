import os

from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(HERE, 'readme.rst')) as f:
    long_description = f.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()

# http://thomas-cokelaer.info/blog/2012/03/how-to-embedded-data-files-in-python-using-setuptools/
datadir = os.path.join('files')
datafiles = [(d, [os.path.join(d, f) for f in files])
    for d, folders, files in os.walk(datadir)]


def get_version():
    version = None
    initpath = os.path.join(HERE, 'faam_wxrx', '__init__.py')
    with open(initpath) as fd:
        for line in fd:
            if line.startswith('__version__'):
                _, version = line.split('=')
                version = version.strip()[1:-1]  # Remove quotation characters
                break
    return version


setup(name = "faam_wxrx",
      version = get_version(),
      description = "python module for working with FAAM Weather Radar Data",
      author = "Axel Wellpott",
      author_email = "axel dot wellpott at faam dot ac dot uk",
      url = "http://www.faam.ac.uk",
      package_dir = {'': '.'},
      packages=find_packages('.'),
      # scripts are defined in the aimms.__init__ file
      entry_points={
          'console_scripts': [
                'faam_wxrx = faam_wxrx:command_line',]
          },
      license='LGPLv3',
      platforms = ['linux', 'windows'],
      long_description = long_description,
      install_requires = [],
      include_package_data = True,
      data_files = datafiles,
      zip_safe = False,     # http://stackoverflow.com/questions/27964960/pip-why-sometimes-installed-as-egg-sometimes-installed-as-files
      keywords = ['FAAM',
                  'Facility for Airborne Atmospheric Measurements',
                  'NCAS',
                  'MetOffice',
                  'data',
                  'science',
                  'meteorology',
                  'ARINC708',
                  'python',
                  'plotting'],
      classifiers = ['Development Status :: 2 - Pre-Alpha',
                     'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
                     'Operating System :: POSIX :: Linux',
                     'Programming Language :: Python',
                     'Programming Language :: Python :: 2',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3',
                     'Programming Language :: Python :: 3.5',
                     'Topic :: Scientific/Engineering'])
