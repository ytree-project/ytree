from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

dev_requirements = [
     'pytest', 'twine', 'pep8', 'flake8', 'wheel',
     'sphinx', 'sphinx-autobuild', 'sphinx_rtd_theme']

setup(name="ytree",
      version="2.2.0.dev1",
      description="An extension of yt for working with merger-tree data.",
      long_description=long_description,
      author="Britton Smith",
      author_email="brittonsmith@gmail.com",
      license="BSD 3-Clause",
      keywords=["simulation", "merger-tree", "astronomy", "astrophysics"],
      url="https://github.com/brittonsmith/ytree",
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
