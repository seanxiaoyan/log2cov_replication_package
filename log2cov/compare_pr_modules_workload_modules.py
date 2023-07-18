import db


L = [
    "salt.utils.extmods",
    "salt.modules.dockermod",
    "salt.utils.jinja",
    "salt.modules.mount",
    "salt.state",
    "salt.states.git",
    "salt.roster.terraform",
    "salt.modules.cmdmod",
    "salt.states.chocolate",
    "salt.modules.zabbix",
    "salt.engines.slack_bolt_engine",
    "salt.modules.xfs",
    "salt.channel.server",
    "salt.utils.versions",
    "salt.output.raw",
    "salt.utils.crypt",
    "salt.renderers.mako",
    "salt.returners.couchbase_return",
    "salt.utils.minion",
    "salt.states.pip_state",
    "salt.utils.slack",
    "salt.matchers.nodegroup_match",
    "salt.modules.bsd_shadow",
    "salt.runners.test",
    "salt.proxy.netmiko_px",
    "salt.utils.vault",
    "salt.utils.yamllint",
    "salt.pillar.http_yaml",
    "salt.utils.pyinstaller.rthooks._overrides",
    "salt.states.rabbitmq_polic",
    "salt.client.ssh.wrapper.pillar",
    "salt.modules.win_event",
    "salt.proxy.napalm",
    "salt.modules.event",
    "salt.utils.vt",
    "salt.pillar.stack",
    "salt.modules.cassandra_mod",
    "salt.utils.x509",
    "salt.modules.vmctl",
    "salt.utils.win_reg",
    "salt.modules.chroot",
    "salt.cache.redis_cache",
    "salt.beacons.network_settings",
    "salt.states.file",
    "salt.modules.xbpspkg",
    "salt.modules.syslog_ng",
    "salt.modules.btrfs",
    "salt.client.ssh.wrapper.state",
    "salt.modules.rpmbuild_pkgbuild",
    "salt.states.win_lgpo_reg",
    "salt.modules.cron",
    "salt.modules.iptables",
    "salt.modules.vsphere",
    "salt.proxy.ssh_sample",
    "salt.modules.ssh",
    "salt.fileclient",
    "salt.modules.vault",
    "salt.utils.event",
    "salt.output.highstate",
    "salt.modules.smartos_virt",
    "salt.runner",
    "salt.modules.namecheap_domains",
    "salt.states.ipset",
    "salt.daemons.masterapi",
    "salt.pillar.netbox",
    "salt.modules.linux_sysctl",
    "salt.syspaths",
    "salt.modules.ipset",
    "salt.runners.vault",
    "salt.utils.rsax931",
    "salt.modules.esxvm",
    "salt.modules.win_wua",
    "salt.renderers.pyobjects",
    "salt.cloud.clouds.libvirt",
    "salt.utils.network",
    "salt.serializers.keyvalue",
    "salt.states.openvswitch_db",
    "salt.modules.pkgng",
    "salt.utils.openstack.neutron",
    "salt.roster.dir",
    "salt.modules.oracle",
    "salt.modules.archive",
    "salt.auth.pam",
    "salt.utils.pkg.__init__",
    "salt.modules.c",
    "salt.loader.context",
    "salt.client.ssh.__init__",
    "salt.pillar.vault",
    "salt.modules.timezone",
    "salt.modules.lxd",
    "salt.payload",
    "salt.modules.virt",
    "salt.cloud.clouds.saltif",
    "salt.pillar.http_json",
    "salt.__init__",
    "salt.states.sysfs",
    "salt.transport.tc",
    "salt.modules.file",
    "salt.modules.prox",
    "salt.modules.zypperpkg",
    "salt.states.iptables",
    "salt.modules.cassandra_cql",
    "salt.modules.opkg",
    "salt.modules.pillar",
    "salt.roster.__init__",
    "salt.modules.purefa",
    "salt.modules.groupadd",
    "salt.netapi.rest_tornado.saltnado",
    "salt.utils.minions",
    "salt.cli.daemons",
    "salt.modules.saltcheck",
    "salt.modules.vboxmanage",
    "salt.renderers.pass",
    "salt.engines.script",
    "salt.modules.pagerduty_util",
    "salt.modules.disk",
    "salt.modules.openvswitch",
    "salt.config.__init__",
    "salt.states.win_dism",
    "salt.utils.schedule",
    "salt.states.ethtool",
    "salt.modules.win_lgpo",
    "salt.modules.servicenow",
    "salt.modules.kmod",
    "salt.modules.pkg_resource",
    "salt.modules.ethtool",
    "salt.states.boto_route53",
    "salt.states.esxi",
    "salt.modules.schedule",
    "salt.utils.win_lgpo_reg",
    "salt.grains.metadata_gce",
    "salt.metaproxy.deltaprox",
    "salt.client.__init__",
    "salt.utils.boto3mod",
    "salt.utils.templates",
    "salt.modules.sdb",
    "salt.modules.gpg",
    "salt.pillar.mongo",
    "salt.modules.mac_brew_pkg",
    "salt.utils.aws",
    "salt.modules.yumpkg",
    "salt.modules.tls",
    "salt.modules.x509_v2",
    "salt.utils.process",
    "salt.returners.cassandra_return",
    "salt.matchers.compound_match",
    "salt.modules.kernelpkg_linux_yum",
    "salt.template",
    "salt.states.macpackage",
    "salt.modules.solarispkg",
    "salt.states.x509_v2",
    "salt.modules.openbsdpkg",
    "salt.states.pkgrepo",
    "salt.netapi.__init__",
    "salt.states.esxcluster",
    "salt.states.glusterfs",
    "salt.netapi.rest_cherrypy.a",
    "salt.roster.sshknownhosts",
    "salt.modules.portage_config",
    "salt.states.zpool",
    "salt.states.influxdb_continuous_quer",
    "salt.utils.job",
    "salt.modules.ps",
    "salt.grains.esxi",
    "salt.modules.win_service",
    "salt.modules.test",
    "salt.states.ansiblegate",
    "salt.modules.pdbedit",
    "salt.modules.mongodb",
    "salt.states.kmod",
    "salt.utils.cloud",
    "salt.loader.laz",
    "salt.spm.__init__",
    "salt.beacons.service",
    "salt.modules.cryptdev",
    "salt.channel.client",
    "salt.client.ssh.wrapper.grains",
    "salt.modules.match",
    "salt.roster.sshconfig",
    "salt.modules.linux_shadow",
    "salt.utils.pycrypto",
    "salt.grains.core",
    "salt.states.htt",
    "salt.states.esxvm",
    "salt.modules.smbios",
    "salt.modules.openbsdrcctl_service",
    "salt.modules.puppet",
    "salt.modules.rh_i",
    "salt.utils.win_network",
    "salt.modules.mac_xattr",
    "salt.utils.pkg.win",
    "salt.modules.parallels",
    "salt.modules.yaml",
    "salt.cloud.clouds.gce",
    "salt.renderers.tomlmod",
    "salt.modules.logrotate",
    "salt.states.schedule",
    "salt.utils.napalm",
    "salt.modules.esxcluster",
    "salt.beacons.watchdog",
    "salt.proxy.esxi",
    "salt.minion",
    "salt.utils.platform",
    "salt.defaults.__init__",
    "salt.modules.napalm_network",
    "salt.states.openvswitch_bridge",
    "salt.modules.win_task",
    "salt.cloud.clouds.azurearm",
    "salt.modules.postgres",
    "salt.modules.telemetr",
    "salt.client.ssh.state",
    "salt.modules.rpm_lowpkg",
    "salt.modules.win_groupadd",
    "salt.states.service",
    "salt.renderers.gpg",
    "salt.states.virt",
    "salt.transport.zeromq",
    "salt.modules.win_file",
    "salt.modules.win_dism",
    "salt.serializers.toml",
    "salt.modules.pkgutil",
    "salt.grains.metadata_azure",
    "salt.utils.path",
    "salt.modules.datadog_api",
    "salt.modules.solaris_fmadm",
    "salt.modules.win_pkg",
    "salt.returners.pgjsonb",
    "salt.states.esxdatacenter",
    "salt.modules.freebsd_sysctl",
    "salt.version",
    "salt.modules.pi",
    "salt.states.pkg",
    "salt.returners.local_cache",
    "salt.roster.flat",
    "salt.returners.mysql",
    "salt.modules.boto_dynamodb",
    "salt.utils.dictdiffer",
    "salt.utils.thin",
    "salt.pillar.__init__",
    "salt.returners.django_return",
    "salt.modules.solarisipspkg",
    "salt.states.x509",
    "salt.modules.mysql",
    "salt.engines.slack",
    "salt.modules.dpkg_lowpkg",
    "salt.runners.mine",
    "salt.modules.win_lgpo_reg",
    "salt.modules.state",
    "salt.modules.splunk",
    "salt.modules.kubeadm",
    "salt.modules.aptpkg",
    "salt.client.mixins",
    "salt.utils.files",
    "salt.cloud.clouds.msazure",
    "salt.modules.rbac_solaris",
    "salt.runners.state",
    "salt.modules.xapi_virt",
    "salt.modules.publish",
    "salt.returners.postgres_local_cache",
    "salt.modules.x509",
    "salt.modules.namecheap_ssl",
    "salt.utils.cache",
    "salt.states.cmd",
    "salt.master",
    "salt.modules.esxdatacenter",
    "salt.renderers.yaml",
    "salt.returners.postgres",
    "salt.utils.pkg.rpm",
    "salt.modules.npm",
    "salt.modules.status",
    "salt.returners.mongo_future_return",
    "salt.modules.nxos_api",
    "salt.cloud.clouds.proxmox",
    "salt.states.mount",
    "salt.modules.esxi",
    "salt.client.ssh.shell",
    "salt.modules.vcenter",
    "salt.modules.pacmanpkg",
    "salt.modules.boto_vpc",
    "salt.modules.chocolate",
    "salt.states.user",
    "salt.runners.saltutil",
    "salt.returners.redis_return",
    "salt.states.saltmod",
    "salt.utils.entrypoints",
    "salt.states.module",
    "salt.scripts",
    "salt.modules.saltutil",
    "salt.states.libcloud_storage",
    "salt.utils.compat",
    "salt.modules.systemd_service",
    "salt.modules.defaults"
]


list_L = [s.replace('.__init__', '') for s in L]


# convert list L to a set for efficient lookups
set_L = set(list_L)

# empty sets to store the module names
modules_in_new_collection = set()
overlap = set()
only_in_L = set()
only_in_new_collection = set()

client = db.Connect.get_connection()
db = client['salt_workloads_module_coverage']
new_collection = db['module_coverage']

# iterate over all documents in the new collection
for document in new_collection.find():
    # fetch the module name
    module_name = document['module_name']

    # add the module name to the set of modules in new collection
    modules_in_new_collection.add(module_name)

    # if the module name is in set L, add it to the overlap set
    if module_name in set_L:
        overlap.add(module_name)

# find module names only in L but not in new collection
only_in_L = set_L - modules_in_new_collection

# find module names only in new collection but not in L
only_in_new_collection = modules_in_new_collection - set_L

print("Overlapping module names:")
print(overlap)

print("Module names only in L:")
print(only_in_L)

print("Module names only in new collection:")
print(only_in_new_collection)