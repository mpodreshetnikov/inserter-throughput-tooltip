#!/bin/sh
# Builds dist/<name>_<version>.zip for the Factorio Mod Portal (mod files only, without dev/).
set -e
cd "$(dirname "$0")"
name=$(sed -n 's/.*"name": *"\([^"]*\)".*/\1/p' info.json)
version=$(sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' info.json)
folder="${name}_${version}"
rm -rf "dist/$folder" "dist/$folder.zip"
mkdir -p "dist/$folder"
cp -r info.json control.lua settings.lua changelog.txt README.md LICENSE thumbnail.png scripts locale "dist/$folder/"
(cd dist && zip -qr "$folder.zip" "$folder" && rm -rf "$folder")
echo "dist/$folder.zip"
