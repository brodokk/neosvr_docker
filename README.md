# NeosVR docker

Based on a work from https://github.com/shiipou/steamcmd but simplified for
only work with NeosVR since I use this mainly for testing the headless client.

Since I don't use this Dockerfile in production I don't recommend you to use
it as is for other thing than testing.

# Usage

You need to be logged as an user to be able to download NeosVR headless client.
For that set `LOGIN` and `PASSWORD` environment variables.

You also need the beta key who can be set via the `BETA-KEY` environment
variable.

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

You can also launch it via docker-compose with the example file
`docker-compose.yml` provided.

After the container is started, you just need attach to it with the following
command if you want to control the server.

```
docker attach <container_name>
```
