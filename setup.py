from setuptools import setup

def get_version(filename):
    """
    Get version from a file.

    Inspired by https://github.mabuchilab/QNET/.
    """
    with open(filename) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip()[1:-1]
    raise RuntimeError(
        "Could not get version from %s." % filename)


VERSION = get_version("ytree/__init__.py")

with open('README.md') as f:
    long_description = f.read()

dev_requirements = [
    'coveralls', 'flake8', 'pytest', 'pytest-cov', 'twine', 'wheel',
    'sphinx', 'sphinx_rtd_theme']

setup(name="ytree",
      version=VERSION,
      description="An extension of yt for working with merger-tree data.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Britton Smith",
      author_email="brittonsmith@gmail.com",
      license="BSD 3-Clause",
      keywords=["simulation", "merger-tree", "astronomy", "astrophysics"],
      url="https://github.com/brittonsmith/ytree",
      project_urls={
          'Homepage': 'https://github.com/brittonsmith/ytree',
          'Documentation': 'https://ytree.readthedocs.io/',
          'Source': 'https://github.com/brittonsmith/ytree',
          'Tracker': 'https://github.com/brittonsmith/ytree/issues'
      },
      packages=["ytree"],
      include_package_data=True,
      classifiers=[
          "Development Status :: 4 - Beta",
          "Environment :: Console",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Astronomy",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: Linux",
          "Operating System :: Unix",
          "Natural Language :: English",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
      ],
      install_requires=[
          'configparser',
          'h5py',
          'numpy',
          'yt>=3.4',
      ],
      extras_require={
          'dev': dev_requirements,
          'rtd': [pkg for pkg in dev_requirements if 'sphinx' not in pkg],
      },
      python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*,!=3.4.*'
)
