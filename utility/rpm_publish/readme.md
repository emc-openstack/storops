# Prerequisites
- On RHEL 7, configure the yum repo first.
```bash
$ cat > /etc/yum.repos.d/common-candidate.repo << EOF
[common-candidate]
name=common-candidate
baseurl=http://cbs.centos.org/repos/cloud7-openstack-common-candidate/x86_64/os
enabled=1
gpgcheck=0
priority=2
EOF
```

- Install package `epel-rpm-macros` which includes the `python-rpm-macros`.

# How to publish storops rpm package

- Find a Redhat machine. Download the `utility/rpm_publish/python-storops.spec` to it.
- Update `Version` and `Change log` in the `python-storops.spec`.
    - Update `Requires` and `BuildRequires` in the `python-storops.spec` if new dependencies are added.
- Run command: `rpmbuild -ba python-storops.spec -v`
    - It will fail quickly if any dependencies is not installed. Install them using `sudo yum install <package_name>`.
- Follow the log on the screen to find the rpm built.

# How to publish storops-vnx rpm package

`storops-vnx` is just a virtual package which depends on `python-storops` and `NaviCli-Linux`.
- Find a Redhat machine. Download the `utility/rpm_publish/python-storops-vnx.spec` to it.
- Update `Version` and `Change log` in the `python-storops-vnx.spec`.
    - Update `Requires` and `BuildRequires` in the `python-storops-vnx.spec` if new dependencies are added.
- Run command: `rpmbuild --target-x86_64 -ba python-storops-vnx.spec -v`
    - It will fail quickly if any dependencies is not installed. Install them using `sudo yum install <package_name>`.
- Follow the log on the screen to find the rpm built.

# How to install storops rpm package

This rpm only supports to be installed in an environment which is deployed the OpenStack.

After deploying OpenStack, run below command to install storops.
`sudo rpm -i <rpm_package_path>`
