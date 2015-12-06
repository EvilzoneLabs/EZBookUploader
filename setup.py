#!/usr/bin/python
"""Process, upload and post ebooks on Evilzone.org"""

from Evilbookup import VERSION
from distutils.core import setup
import platform

WIN32 = (platform.system() == "Windows")

if WIN32:
    import py2exe

setup_kwargs = dict(
    name="evilbookup",
    version=VERSION,
    description="Process, upload and post ebooks on Evilzone.org",
    author="kenjoe41",
    author_email="kenjoe41@evilzone.org",
    url="https:/evilzone.org",
    packages=[  
        "Evilbookup/",
    ],
    scripts=[
      "bin/evilbookup",
	  ],
    license="GNU Public License v3.0",
    long_description=" ".join(__doc__.strip().splitlines()),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    options={
        'sdist': {
            'formats': 'zip',
        }
    }    
)
    
setup(**setup_kwargs)
