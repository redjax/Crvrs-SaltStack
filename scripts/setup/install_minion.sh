#!/bin/bash

## Detect distribution
DISTRO=$(lsb_release -is)
if [ -z $DISTRO ]; then
    DISTRO='unknown'
fi

read -p "IP or FQDN of Salt master node: " SALT_MASTER
CMD_BASE="sudo sh install_salt.sh"
MINION_ID=$HOSTNAME

echo "Installing Salt Minion on [$DISTRO]. Minion ID: $MINION_ID"

if [[ ! -f "install_salt.sh" ]]; then
    curl -L https://bootstrap.saltstack.com -o install_salt.sh
fi

if [[ $DISTRO == "Ubuntu" ]]; then
    if [ -z $SALT_MASTER ]; then
        echo "Pointing to master: $SALT_MASTER"
        $CMD_BASE -P stable -A $SALT_MASTER
    else
        $CMD_BASE -P stable
    fi
else
    if [ -z $SALT_MASTER ]; then
        echo "Pointing to master: $SALT_MASTER"
        $CMD_BASE -A $SALT_MASTER
    else
        $CMD_BASE
    fi
fi

if [[ -f "install_salt.sh" ]]; then
    echo "Removing ./install_salt.sh"
    rm ./install_salt.sh
fi

if [ -z ufw ]; then
    echo "Allowing ports 4505, 4506 through firewall"
    sudo ufw allow 4505
    sudo ufw allow 4506

    echo "Reloading firewall"
    sudo ufw reload
else
    echo "UFW not installed. Please allow ports 4505 & 4506 through your firewall for Salt to function properly."
fi
