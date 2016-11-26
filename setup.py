#!/usr/bin/env python3
from setuptools import setup
import re
 
 
version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('trapdoor/trapdoor.py').read(),
    re.M
    ).group(1)
 
 
# with open("README.md", "rb") as f:
#     long_descr = f.read().decode("utf-8")
 
 
setup(
    name="trapdoor",
    version=version,
    packages = ["trapdoor"],
    description="recieve/store snmp traps & filter them",
    # long_description=long_descr,
   
    entry_points = {
        "console_scripts": ['trapdoor = drapdoor.cli:main']
    },
    install_requires= [
    
        "pysnmp",
        "js2py",
        "aiohttp",
        "janus",
        "sqlalchemy",
        "pymysql",
        "aiomysql",
	"pyyaml",
	"passlib"
        
    ],
    #tests_require=["requests_mock"],
    test_suite="tests"
    
)
