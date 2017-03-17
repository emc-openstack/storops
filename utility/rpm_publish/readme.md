# How to publish storops rpm package

- cd to `rpm_publish`.
- Download the pypi packages which to be packaged to the rpm, and put them
  under folder `pip_packs`.
- Update `Version` and `Change log` in the `storops_rpm_spec`.
- Run command: `rpmbuild -ba storops_rpm.spec -v`
- Follow the log on the screen to find the rpm built.

*NOTE* all pypi packages under `rpm_publish/pip_packs` will be packaged to the
rpm.


# How to install storops rpm package

Make sure the host has `pip`, `gcc`, `python header files`, `ssl header files`
installed.
If not, use below commands to install.
- sudo yum install python-pip
- sudo yum install gcc.x86_64
- sudo yum install python-devel.x86_64
- sudo yum install openssl-devel.x86_64
