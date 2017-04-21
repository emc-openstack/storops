# How to publish storops rpm package

- cd to root directory where the `requirements.txt` is.
- Update `Version` and `Change log` in the `utility/rpm_publish/storops_rpm.spec`.
- Run command: `rpmbuild -ba storops_rpm.spec -v`
- Follow the log on the screen to find the rpm built.


# How to install storops rpm package

Make sure the host has `pip` installed.
If not, use below commands to install.
- sudo yum install python-pip
