#! /usr/bin/bash

# run as: osp_deploy.sh [arg1, arg2, ...]
# args could be: (check in order)
# 1. local rpm file paths.
# example: osp_deploy.sh storops.rpm cachez.rpm
# 2. a specified release version of storops on github.
# example: osp_deploy.sh 0.5.7
# 3. the latest version of storops on github when no args passed in.

# run on the undercloud node
# assumes the latest rhosp-director-images is installed and unpacked
# assumes there is an overcloud-full.qcow file in the directory the script is
# run in

if [ ! -f overcloud-full.qcow2 ]; then
    echo "must be run in a directory containing overcloud-full.qcow2"
    exit 1
fi

if [ -n "$1" -a -f "$1" ]; then
    mkdir -p newpkgs
    echo "using local rpm files: $@"
    cp $@ newpkgs/
else
    . $(dirname $0)/download_pkgs.sh newpkgs $1
fi

virt-copy-in -a overcloud-full.qcow2 newpkgs /root
virt-customize -a overcloud-full.qcow2 --run-command "yum localinstall -y /root/newpkgs/*.rpm" --run-command "rm -rf /root/newpkgs"

