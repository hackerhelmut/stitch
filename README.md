# Stitch Orchestration System

Stitch is a server orchestration system based on ssh, fabric, fabtools and yarn.
All configuration values are stored in a yarn yaml folder structure.

Stitch has the ability to update the yaml files on the fly if needed.

## Folder structure

Stitch configurations are stored in a database directory which is structured in the following way:

- host directory with a yaml file for each host
- services directory with a yaml file for each service
- user directory with a yaml file for each user

## Host files

The host file may contain the following details, and more:

- hostname - a hostname which has to be the same as the file name.
- service - a dict containing options for all activated services of the host
- defaults - a dict containing commonly used defaults

```yaml
```

## Service file

- name -  the name of the service
- install - a structure defining the packages which need to be installed (distribution specific)
- fs - a list of dict for files and directories
- script - the code of an executable to be executed on the host.
- defaults - a dict containing commonly used defaults

```yaml
```

## User file

```yaml
```

## Usage

```bash
cd <yaml database directory>
stitch deploy <hostname> # To update all services and users on that host
stitch deploy <hostname> --user <username> # To update the user <username> on that host
stitch deploy <hostname> --service <servicename> # To update the service <servicname> on that host
```

## License

Apache License 2.0 (Apache-2.0)
