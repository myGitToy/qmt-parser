安装tushare
1.下载最新版软件python3支持（版本号查询地址https://docs.anaconda.com/anaconda/install/linux）：
curl -O https://repo.continuum.io/archive/Anaconda3-5.0.1-Linux-x86_64.sh

2. 运行安装程序python3：
bash Anaconda3-5.0.1-Linux-x86_64.sh

3.下载最新版软件python2（版本号查询地址https://docs.anaconda.com/anaconda/install/linux）：
curl -O https://repo.continuum.io/archive/Anaconda2-5.0.1-Linux-x86_64.sh

4. 运行安装程序python2：
bash Anaconda2-5.0.1-Linux-x86_64.sh

5.安装BeautifulSoup4（否则会报错No Module Named bs4）
pip install BeautifulSoup4

6.安装其余支持文件，如pandas/numpy/lxml等等，默认已经通过anaconda/miniconda等安装完毕
miniconda下的命令如下：
python -V
conda install numpy
conda install pandas
conda install matplotlib

6.安装主文件
pip install tushare