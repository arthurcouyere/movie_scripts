#!/bin/bash

echo "# ufw reset"
sudo ufw --force reset

echo "# ufw enable"
sudo ufw enable

echo "# ufw deny all trafic"
sudo ufw default deny outgoing
sudo ufw default deny incoming

echo "# ufw allow on tun0 (vpn)"
sudo ufw allow out on tun0 from any to any
sudo ufw allow in on tun0 from any to any

echo "# ufw allow DNS"
sudo ufw allow out 53
sudo ufw allow in 53

# allow vpn servers (list from network manager)
vpn_server_list=$(sudo cat /etc/NetworkManager/system-connections/*.nmconnection | grep "remote=" | cut -d"=" -f2 | cut -d":" -f1)
for vpn_server in $vpn_server_list; do
    vpn_server_ip=$(dig +short $vpn_server)
    echo "# ufw allow vpn server: $vpn_server [$vpn_server_ip]"
    sudo ufw allow out from any to $vpn_server_ip
done