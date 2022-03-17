#!/usr/bin/env bash
#creating CA private key and certificate
openssl genrsa 2048 > ca-key.pem
openssl req -new -x509 -nodes -days 3650 -key ca-key.pem -subj "/C=RU/O=Net Lan/CN=net.lan" -out ca-cert.crt

#creating certificates
openssl req -newkey rsa:2048 -nodes -days 3650 -keyout server-key.pem -subj "/C=RU/O=Net Lan/CN=*.net.lan" -out server-request.pem
openssl x509 -req -days 3650 -set_serial 01 -extfile <(printf "subjectAltName=DNS:*.net.lan") -in server-request.pem -out server-cert.pem -CA ca-cert.crt -CAkey ca-key.pem

#sudo cp ca-cert.crt /usr/local/share/ca-certificates/
#sudo update-ca-certificates
