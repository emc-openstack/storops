#! /usr/bin/bash

# run as: osp_deploy.sh [arg1]
# arg1 could be: (check in order)
# 1. a local rpm file path.
# 2. a specified release version on github.
# 3. the latest version on github when arg1 is omitted.

# run on the undercloud node
# assumes the latest rhosp-director-images is installed and unpacked
# assumes there is an overcloud-full.qcow file in the directory the script is
# run in

if [ ! -f overcloud-full.qcow2 ]; then
    echo "must be run in a directory containing overcloud-full.qcow2"
    exit 1
fi

# need these packages installed
sudo yum install -y libguestfs-tools-c wget

if [ -n "$1" -a -f "$1" ]; then
    mkdir newpkgs
    echo "using local rpm file: $1"
    cp "$1" newpkgs/
else
    release='latest'
    [ -n "$1" ] && release="tags/r$1"

    rel_info="$(curl -s https://api.github.com/repos/emc-openstack/storops/releases/$release)"
    if [[ $rel_info == *"\"message\": \"Not Found\""* ]]; then
        echo "invalid release."
        exit 1
    fi

    download_url=$(echo "$rel_info" | grep -oh "browser_download_url\": \".*\"" | cut -d' ' -f2 | cut -d'"' -f2)
    echo "$download_url"
    if [ -z "$download_url" ]; then
        echo "no rpm url found."
        exit 1
    fi

    mkdir newpkgs
    cd newpkgs
    echo "using rpm file: $download_url"
    wget $download_url
    cd ..
fi

virt-copy-in -a overcloud-full.qcow2 newpkgs /root
virt-customize -a overcloud-full.qcow2 --run-command "yum localinstall -y /root/newpkgs/*rpm" --run-command "rm -rf /root/newpkgs"

