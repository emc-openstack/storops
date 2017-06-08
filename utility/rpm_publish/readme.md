# How to publish storops rpm package

- Find a Fedora machine. Download the `utility/rpm_publish/python-storops.spec` to it.
- Update `Version` and `Change log` in the `python-storops.spec`.
    - Update `Requires` and `BuildRequires` in the `python-storops.spec` if new dependencies are added.
- Run command: `rpmbuild -ba storops_rpm.spec -v`
    - It will fail quickly if any dependencies is not installed. Install them using `sudo dnf install <package_name>`.
- Follow the log on the screen to find the rpm built.


# How to install storops rpm package

This rpm only supports to be installed in an environment which is deployed the OpenStack.
Because this rpm only contains some dependencies not included in OpenStack.

After deploying OpenStack, run below command to install storops.
`sudo rpm -i <rpm_package_path>`
