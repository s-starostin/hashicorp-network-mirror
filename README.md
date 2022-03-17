hashicorp-proxy
=========
Registry proxy server for Hashicorp Terraform.\
If you have HTTP file server with some terraform providers and directory structure like this: https://somedomain.com/terraform-provider-vault/3.3.1/terraform-provider-vault_3.3.1_linux_amd64.zip
, using this software you can convert it to a terraform network mirror that uses the protocol described here - https://www.terraform.io/internals/provider-network-mirror-protocol.

You'll have to define routes in `routes` in `config.yaml` to setup mapping according to your server catalog structure.
By default this proxy configured to act as a terraform network mirror, but if you comment out `providers_subpath` and `routes` it will act as http file server for directory defined in `directory`.

According to the mirror specification protocol the content must be served over HTTPS. To meet this requirement you can create self-signed certificates using `setup-ssl-certificates.sh`, but this proxy can also run as HTTP server.\
To configure caching of generated JSON files to speed up performance, a caching proxy with [SSL termination](https://www.f5.com/services/resources/glossary/ssl-termination) (such as nginx) can be set up in front of this server.
Note that by default this proxy runs on either 80 or 443 port which are [priveleged ports](https://www.w3.org/Daemon/User/Installation/PrivilegedPorts.html).

This proxy calculates [hashes](https://www.terraform.io/internals/provider-network-mirror-protocol#hashes) for each zip archive on the fly using Terraform's provider package hashing algorithm, using [HashZip](https://pkg.go.dev/golang.org/x/mod/sumdb/dirhash#HashZip), the same way `terraform providers mirror` command does.

CLI-parameters
----------------
| Argument | Default | Comment |
| ------ | ------- | ------- |
| --config-file, -c | config.yaml | server configuration file path |
| --directory, -d | files | directory to serve |
| --host, -H | localhost | server host |
| --port, -p | 80 | server port |
| --ssl-enabled | False | use HTTPS |
| --ssl-check-hostname | False | enable [hostname checking](https://docs.python.org/3/library/ssl.html#ssl.SSLContext.check_hostname) |    
| --ssl-server-cert | server-cert.pem | server certificate file |
| --ssl-server-cert-key | server-key.pem | server certificate key file |
