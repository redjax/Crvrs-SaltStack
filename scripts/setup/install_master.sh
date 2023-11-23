#!/bin/bash

## Detect distribution
DISTRO=$(lsb_release -is)
if [ -z $DISTRO ]; then
    DISTRO='unknown'
fi

echo "Installing Salt Master on [$DISTRO]"

if [[ ! -f "install_salt.sh" ]]; then
    curl -L https://bootstrap.saltstack.com -o install_salt.sh
fi

if [[ $DISTRO == "Ubuntu" ]]; then
    sudo sh install_salt.sh -M -P stable
else
    sudo sh install_salt.sh -M
fi

if [[ -f "install_salt.sh" ]]; then
    echo "Removing ./install_salt.sh"
    rm ./install_salt.sh
fi
