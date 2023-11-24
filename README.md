# Crvrs SaltStack

Repository for learning [SaltStack](https://saltproject.io). This repository is a mix of dev/learning modules, and live/production Salt resources.

The included [`salt-ctrl`](./salt-ctrl/) is a Python utility for generating scripts to run on master/minion nodes. Over time it may grow to more complex operations like copying/executing the scripts on the remote.

## Notes

### Port requirements

| Port  |                            Type                            |          Description          |
| :---: | :--------------------------------------------------------: | :---------------------------: |
| 4505  |   Event Publisher/Subscriber port (publish jobs/events)    | Constant inquiring connection |
| 4506  | Data payloads & minion returns (file services/return data) | Connects only to deliver data |

### Bootstrap SaltStack installation

[Commonly used bootstrap script options](https://docs.saltproject.io/salt/install-guide/en/latest/topics/bootstrap.html#commonly-used-bootstrap-script-options)
[Additional bootstrap script options](https://docs.saltproject.io/salt/install-guide/en/latest/topics/bootstrap.html#additional-bootstrap-script-options)

- `-M`: Install as Salt master
- `-P`: Install from packages. Use `pip` if that fails
- `-U`: Update all packages through OS system's package manager. This takes a long time.
- `-A <ip-address>`: Declare IP/FQDN of Salt master that minion will connect to.
  - Ex: `boostrap-salt.sh -A 192.168.1.5 stable 3006.4`
    - Install Salt, point to `192.168.1.5` for the master node, install Salt version 3006.4 stable
  - Creates `/etc/salt/minion.d/99-master-address.conf` file
- `-i <some-minion-id>`: Set the `/etc/salt/minion_id` file to the given ID. If not defined, defaults to minion's hostname.

#### Master node

Install SaltStack with the convenience script and `-M` flag (for "master")

```
curl -L https://bootstrap.saltstack.com -o install_salt.sh
sudo sh install_salt.sh -M
```

**NOTE**: On Ubuntu nodes, you must also use `-P stable`. The `-P` option installs packages with pip if they are not found.

After installing Salt on minion node(s), accept their keys on the master.

- Check keys: `salt-key -L`
- Accept all keys: `salt-key -A`

#### Minion node(s)

On each minion, install with the convenience script, omitting the `-M` flag

```
curl -L https://bootstrap.saltstack.com -o install_salt.sh
sudo sh install_salt.sh
```

**NOTE**: On Ubuntu nodes, you must also use `-P stable`. The `-P` option installs packages with pip if they are not found.

If you did not install Salt on the minion with the `-A` flag (specifying a Salt master IP/FQDN), edit `/etc/salt/minion` file, changing the line `# master: salt` to `master: <ip/fqdn>`.

#### Salt key management

On the Salt master, you can quickly view all Salt minion connections and view whether the connection is accepted, rejected, or pending.

```
salt-key --list-all
```

Before Salt minions can connect to the master, you need to accept the minion's key on the master node:

```
salt-key --accept=<key>
```

Optionally, but not recommended, you can accept all minion keys:

```
salt-key --accept-all
```

#### Configuring the Salt hostname

Salt minions attempt to contact the Salt master using the `salt` hostname. If you don't have DNS in your environment, or if the Salt master hostname is something other than `salt`, you can add the IP address of your Salt master server to the `/etc/salt/minion` configuration file by changing the `master` setting.

### Ad-Hoc commands

Run ad-hoc commands with `salt` from the Master node. To check connectivity between the salt Master and a minion (or all minions, with `salt "*"`), run `salt "*" test.version`. This will print the minion's Salt version, proving a successful connection.

#### Helpful commands to know

- `test.version`: Print the minion's Salt version
- `cmd`: Run shell commands
  - Ex: `salt "*" cmd.run "ls -l /etc/"`
- `pkg`: Maps local system package managers to the same salt functions. Examples:
  - `pkg.install`: Install a package using the OS's package manager
    - Ex: `salt "*" pkg.install vim` / `salt "*" pkg.uninstall vim`
- `network.interfaces`: List all interfaces on a minion
  - Ex: `salt "*" network.interfaces`
- Utilize Salt [`Grains`](https://docs.saltproject.io/en/latest/topics/grains/index.html)
  - List available grains with `salt "*" grains.ls`
  - List grain data with `salt "*" grains.items`

## Links

- [SaltStack Docs](https://docs.saltproject.io/en/latest)
- [SaltStack Docs: Salt in 10 Minutes](https://docs.saltproject.io/en/latest/topics/tutorials/walkthrough.html)
- [SaltStack Docs: Manual install directions by operating system](https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/index.html#install-by-operating-system-index)
  - [Windows](https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/windows.html)
  - [Debian](https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/debian.html)
  - [Ubuntu](https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/ubuntu.html)
  - [Fedora](https://docs.saltproject.io/salt/install-guide/en/latest/topics/install-by-operating-system/fedora.html)
- [SaltStack Docs: Installing SaltStack](https://docs.saltproject.io/en/getstarted/fundamentals/install.html)
  - For quick bootstrap commands, check the linked text "Show me how to install using bootstrap" under the `Install` section.
  - For full SaltStack installation instructions, check the [full installation docs](https://docs.saltproject.io/salt/install-guide/en/latest/)
- [SaltStack Docs: Execution Modules Ref](https://docs.saltproject.io/en/latest/ref/modules/all/index.html)
- [Linode: Salt reference/guide articles](https://www.linode.com/docs/guides/applications/configuration-management/salt/)
- [Github: SaltStack Formulas](https://github.com/saltstack-formulas)
