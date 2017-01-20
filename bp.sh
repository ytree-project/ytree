# install conda and yt dependencies with conda
cd ..
wget --quiet https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
bash ./Miniconda2-latest-Linux-x86_64.sh -b -p ./ytree-conda -f
export PATH=$PWD/ytree-conda/bin:$PATH
conda install -q -y mercurial cython h5py matplotlib sympy numpy pytest flake8 configparser

# set up development build of yt
hg clone https://bitbucket.org/yt_analysis/yt yt-hg
cd yt-hg
hg up yt
pip install -e .
cd ..

# download test data
hg clone https://bitbucket.org/brittonsmith/ytree_test_data

# install ytree now that it's been downloaded
cd ytree
pip install -e .

# start the tests themselves
py.test tests
