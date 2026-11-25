#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p Resources
cp "../全景建筑版/深圳湾_全景建筑.html" Resources/Atlas.html
xcodegen generate
