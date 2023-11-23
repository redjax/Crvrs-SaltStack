#!/bin/bash

echo ""
echo "This script assumes you are using UFW for firewall management."
echo "If you are using another firewall management utility, allow the following 2 ports manually:"
echo ""
echo "4505, 4506"
echo ""

sudo ufw allow 4505
sudo ufw allow 4506
