# NeosVR docker

Based on a work from
[shiipou GitHub repository](https://github.com/shiipou/steamcmd) but simplified
for only work with NeosVR since I use this mainly for testing the headless
client.

Since I don't use this Dockerfile in production I don't recommend you to use
it as is for other thing than testing.

See NeosVR official [wiki page](https://wiki.neos.com/Headless_Client/Server)
for more information about the headless client.

# Usage

You need to be logged as an user to be able to download NeosVR headless client.
For that set `LOGIN` and `PASSWORD` environment variables.

You also need the beta key who can be set via the `BETA-KEY` environment
variable.

## Simple usage

Before using it you need to build it and then use it, for example,  directly
via docker with the following commands. Keep in mind this took some time, so be
patient.

```
docker build -t neosvr_headless .
docker run -it -v "steam:/steam" -v "neosvr.conf.json:/steam/740250/Config/Config.json" -e BETA_NAME=headless-client -e BETA_KEY=**** -e LOGIN=user -e PASSWORD=pwd neosvr_headless
```

Tips: if you have some problems you can launch a bash (or everything who start
by `/`) to the docker run command.

If needed you can also overwrite the `INSTALL_APPS` and `LAUNCH_APP`
environement variables. The first one is usefull if you need to install more
apps than one (this is a string where apps ids are separated by `,` without
spaces) but not needed actually for the NeosVR headless client. And the second
environement variable is for define the app to be launched at start. Both have
as default value the actual NeosVR headless client id `740250`.

## Docker Compose

You can also launch it via docker-compose with the example file
`docker-compose.yml` provided.

After the container is started, you just need attach to it with the following
command if you want to control the server.

```
docker attach <container_name>
```

## Docker Compose with portainer

You can also use this with this portainer. Launch the stack in
`docker-compose_portainer.yml` and then import the normal
`docker-compose.yml` via the web interface.

```
docker-compose -f docker-compose_portainer.yml up
```

You will need to replace the three following string in the compose file for
make it work: `<EMAIL>`, `<PASSWORD>`, `<DOMAIN>`.

For generate password you will need to use the following command (replace `mycutepassword` by your password):

```
docker run --rm httpd:2.4-alpine htpasswd -nbB admin 'mycutepassword' | cut -d ":" -f 2
```

And the add `$` in front of all the `$` otherwise you will have a parsing error.
More information here: https://gist.github.com/deviantony/62c009b41bde5e078b1a7de9f11f5e55

# scripts

## Neos Headless RCON Websocket

Enable remote access to Neos headless server console via secure websocket within Neos userspace.

Thanks to GrayBoltWolf for his script, you can check the original one here: https://gitlab.com/-/snippets/2249980.

NeosVR facet/panel can be found in his public folder: neosrec:///U-GrayBoltWolf/R-6ab7ea3e-b7a9-4ab7-9490-955094c34021

In the futur i will make this script with a better integration with the current docker stack. Just a little todolist formyself:

- Automatic detection of the headless
- Automatic setup of the certificate
- Still support non-docker installation

### Installation

The following packages are needed:

```
websockets
pexpect
```

You need to set the id of the container line `71`.

And last but not least dont forgot to set the key in the `accesscode.txt` file.
Can be anything, but keep in mind security.

# Notes

If you have frequent GC crashes you need to set `vm.max_map_count=262144` in
`/etc/sysctl.conf`.
