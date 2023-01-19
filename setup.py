from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in authentication_module/__init__.py
from authentication_module import __version__ as version

setup(
	name="authentication_module",
	version=version,
	description="Authentication API For Mobile Application",
	author="Jigar Tarpara",
	author_email="jigartarpara@khatavahi.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
