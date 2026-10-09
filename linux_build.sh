#!/bin/bash
#build file for linux

#remove old builds
if [ -d "./dist/chronocrash-modders-tools" ];
then
rm -rf "./dist/chronocrash-modders-tools"
fi
if [ -d "./build" ];
then
rm -rf "./build"
fi

#run installer
#--paths . is required: the repo root contains an __init__.py, so PyInstaller
#treats it as a package and would otherwise look for common/gui/... one level up.
pyinstaller --clean --paths . --name "chronocrash-modders-tools" ./cmt.py

#copy directories
#PyInstaller >= 6 puts the bundled modules in _internal/, and only that
#directory is on sys.path. Older versions kept them next to the executable.
if [ -d "./dist/chronocrash-modders-tools" ];
then
if [ -d "./dist/chronocrash-modders-tools/_internal" ];
then
DEST="./dist/chronocrash-modders-tools/_internal"
else
DEST="./dist/chronocrash-modders-tools"
fi
cp -r ./data ./common ./gui ./guilib ./icons ./other ./qutepart ./templates ./themes "$DEST"
fi
