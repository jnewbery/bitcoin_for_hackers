# Bitcoin for Hackers

A demonstration of interesting technical topics in Bitcoin.

### Pre-Requisites

##### Install python 3.5 or above on your machine:

- Windows: https://www.python.org/ftp/python/3.6.2/python-3.6.2-amd64.exe
- Mac OS X: https://www.python.org/ftp/python/3.6.2/python-3.6.2-macosx10.6.pkg
- Linux: see your distro docs

##### Install pip:

Download this script: https://bootstrap.pypa.io/get-pip.py

Run (you may need to specify python3 if you also have python2 installed)

```
$ python get-pip.py
```

##### Install git:

```
https://git-scm.com/downloads
```

### Install requirements

```
$ git clone https://github.com/jnewbery/bitcoin_for_hackers
$ cd bitcoin_for_hackers
$ python3 -m venv .venv
```

##### Linux/OSX:

```
$ . .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```

##### Windows:

```
> .venv\Scripts\activate.bat
> pip install -r requirements.txt
```

### Run jupyter notebook

```
(.venv) $ jupyter notebook
```
