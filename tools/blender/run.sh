#!/bin/bash
# обёртка: ./run.sh <аргументы build.py>
cd "$(dirname "$0")"
"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --factory-startup --python build.py -- "$@" 2>&1 | grep -v "^Fra:\|^ *$\|Sample \|CUEW\|Blender quit\|^Blender 5" | tail -40
