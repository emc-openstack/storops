#! /usr/bin/bash

# run as: osp_deploy.sh [arg1, arg2, ...]
# args could be: (check in order)
# 1. local rpm file paths.
# example: osp_deploy.sh storops.rpm cachez.rpm
# 2. a specified release version of storops on github. (latest version is used
# when the args are omitted.
# example: osp_deploy.sh 0.5.7
# example: osp_deploy.sh
# 3. support download rpm packages only, using `download`.
# example: osp_deploy.sh download 0.5.7

# run on the undercloud node
# assumes the latest rhosp-director-images is installed and unpacked
# assumes there is an overcloud-full.qcow file in the directory the script is
# run in

[ -n "$1" -a "$1" == "download" ] && download=1 && shift

if [ -z "${download}" -a ! -f overcloud-full.qcow2 ]; then
    echo "must be run in a directory containing overcloud-full.qcow2"
    exit 1
fi

if [ -n "$1" -a -f "$1" ]; then
    mkdir -p newpkgs
    echo "using local rpm files: $@"
    cp $@ newpkgs/
else
    mkdir -p newpkgs
    cd newpkgs

    sudo yum install -y curl

    release='latest'
    [ -n "$1" ] && release="tags/r$1"

    git_repos="emc-openstack/storops/releases/${release} \
               peter-wangxu/persist-queue/releases/tags/v0.2.3 \
               jealous/cachez/releases/tags/r0.1.2 \
               jealous/retryz/releases/tags/r0.1.9"

    wget_urls="http://cbs.centos.org/kojifiles/packages/python-bitmath/1.3.1/1.el7/noarch/python2-bitmath-1.3.1-1.el7.noarch.rpm \
               https://github.com/emc-openstack/naviseccli/raw/master/NaviCLI-Linux-64-x86-en_US-7.33.9.1.55-1.x86_64.rpm"

    for repo in ${git_repos}; do

        rel_info="$(curl -s https://api.github.com/repos/${repo})"
        if [[ ${rel_info} == *"\"message\": \"Not Found\""* ]]; then
            echo "invalid release."
            exit 1
        fi

        download_url=$(echo "${rel_info}" | grep -oh "browser_download_url\": \".*\"" | grep ".rpm" | cut -d' ' -f2 | cut -d'"' -f2)
        if [ -z "${download_url}" ]; then
            echo "no rpm url found."
            exit 1
        fi
	
        for url in ${download_url}; do
            echo "downloading rpm from: ${url}"
            curl -sSOL ${url}
        done
    done

    for url in ${wget_urls}; do
        echo "downloading rpm from: ${url}"
        curl -sSOL ${url}
    done

    cd ..
fi

[ -n "${download}" ] && exit 0

# need these packages installed
sudo yum install -y libguestfs-tools-c

virt-copy-in -a overcloud-full.qcow2 newpkgs /root
virt-customize -a overcloud-full.qcow2 --run-command "yum localinstall -y /root/newpkgs/*.rpm" --run-command "rm -rf /root/newpkgs"

