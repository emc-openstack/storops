# How to publish storops rpm package

- cd to root directory where the `requirements.txt` is.
- Update `Version` and `Change log` in the `utility/rpm_publish/storops_rpm.spec`.
- Run command: `rpmbuild -ba utility/rpm_publish/storops_rpm.spec -v`
- Follow the log on the screen to find the rpm built.


# How to install storops rpm package

This rpm only supports to be installed in an environment which is deployed the OpenStack.
Because this rpm only contains some dependencies not included in OpenStack.

After deploying OpenStack, run below command to install storops.
`sudo rpm -i <rpm_package_path>`
