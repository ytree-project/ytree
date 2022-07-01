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
        f"Could not get version from {filename}.")


VERSION = get_version("ytree/__init__.py")

with open('README.md') as f:
    long_description = f.read()

dev_requirements = [
    'codecov', 'flake8', 'pydot', 'pytest>=3.6', 'pytest-cov', 'twine',
    'wheel', 'sphinx', 'sphinx_rtd_theme']

setup(name="ytree",
      version=VERSION,
      description="An extension of yt for working with merger tree data.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Britton Smith",
      author_email="brittonsmith@gmail.com",
      license="BSD 3-Clause",
      keywords=["simulation", "merger tree", "astronomy", "astrophysics"],
      url="https://github.com/ytree-project/ytree",
      project_urls={
          'Homepage': 'https://github.com/ytree-project/ytree',
          'Documentation': 'https://ytree.readthedocs.io/',
          'Source': 'https://github.com/ytree-project/ytree',
          'Tracker': 'https://github.com/ytree-project/ytree/issues'
      },
      packages=["ytree"],
      include_package_data=True,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Astronomy",
          "License :: OSI Approved :: BSD License",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: Linux",
          "Operating System :: Unix",
          "Natural Language :: English",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Programming Language :: Python :: 3.10",
      ],
      install_requires=[
          'configparser',
          'h5py',
          "more_itertools>=8.4",
          'numpy',
          'unyt',
          'yt>=4.0',
      ],
      extras_require={
          'dev': dev_requirements,
          'rtd': [pkg for pkg in dev_requirements if 'sphinx' not in pkg],
          'parallel': ['mpi4py'],
      },
      python_requires='>=3.7'
)
