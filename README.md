# Repeater
an automation tool that can repeat any task once recorded. 

Useful for any scenario that involves repitive, cyclic activity, from copy-pasting row-upon-row of information from one database to another, or AFK farming for your favorite video games!

[Download (.py)](MuxRepeat.py) - requires installation of additional packages to work

[Download (.exe)](https://github.com/s2bd/universal-macro-automation/releases/tag/v0.1) - for Windows, ready-to-use

## Compilation

```python
pip install customtkinter pynput pyinstaller
```
```python
pyinstaller --onefile --windowed --icon=MuxRepeater.ico MuxRepeat.py
```
or
```python
python -m PyInstaller --onefile --windowed --icon=MuxRepeater.ico MuxRepeat.py
```
