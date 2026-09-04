#!/usr/bin/env zsh
target=$1

sed -i -E "s/targetIP=.*?/targetIP=$1/" ~/.zshrc
export targetIP=$1
echo "Target is:" $targetIP
source ~/.zshrc