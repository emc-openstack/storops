#!/usr/bin/env bash

function die()
{
    echo "ERROR!!!" ; exit 1
}

mkdir -p gen_yum_install && cd gen_yum_install || die

curl -s https://raw.githubusercontent.com/emc-openstack/storops/develop/utility/osp_deploy.sh \
    | bash -s download || die
cd newpkgs && tar -pczf ../storops_rpms.tar.gz * && cd .. && rm -rf newpkgs || die

cat <<EOF > yum_install_storops.sh
#!/bin/bash
function die()
{
    echo "ERROR!!!" ; exit 1
}

echo "Installing storops and its dependencies..."

cd \$(dirname \$0) \
    && mkdir -p storops_install \
    && tail -n1 \$0 | base64 -d | tar -pzxf - -C ./storops_install || die

cd storops_install \
    && sudo yum localinstall -y ./*.rpm >../yum_install_storops.log 2>&1 \
    && cd .. && rm -rf storops_install || die

exit \$?
EOF

base64 -w 0 storops_rpms.tar.gz >> yum_install_storops.sh \
    && chmod ug+x yum_install_storops.sh && cp yum_install_storops.sh .. \
    && cp storops_rpms.tar.gz .. && rm -rf yum_install_storops || die
