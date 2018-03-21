#! /usr/bin/bash

# run as: download_pkgs.sh [arg1, arg2]
# args could be: (check in order)
# 1. the directory rpms store
# example: download_pkgs.sh pkgs_dir
# 2. a specified release version of storops on github.
# example: download_pkgs.sh 0.5.7
# 3. the latest version of storops on github when no version passed in.

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0 package_directory [storops_version]"
    exit 1
fi

# need these packages installed
sudo yum install -y curl

mkdir -p $1
cd $1

release='latest'
[ -n "$2" ] && release="tags/r$2"

git_repos="emc-openstack/storops/releases/$release \
           peter-wangxu/persist-queue/releases/tags/v0.2.3 \
           jealous/cachez/releases/tags/r0.1.2 \
           jealous/retryz/releases/tags/r0.1.9"

rpm_urls="http://cbs.centos.org/kojifiles/packages/python-bitmath/1.3.1/1.el7/noarch/python2-bitmath-1.3.1-1.el7.noarch.rpm \
           https://github.com/emc-openstack/naviseccli/raw/master/NaviCLI-Linux-64-x86-en_US-7.33.9.1.55-1.x86_64.rpm"

for repo in ${git_repos}; do

    rel_info="$(curl -s https://api.github.com/repos/$repo)"
    if [[ ${rel_info} == *"\"message\": \"Not Found\""* ]]; then
        echo "invalid release."
        exit 1
    fi

    download_url=$(echo "$rel_info" | grep -oh "browser_download_url\": \".*\"" | grep ".rpm" | cut -d' ' -f2 | cut -d'"' -f2)
    echo "${download_url}"
    if [ -z "$download_url" ]; then
        echo "no rpm url found."
        exit 1
    fi

    echo "downloading rpm from: $download_url"
    curl -L ${download_url} -O . >/dev/null 2>&1
done

for url in ${rpm_urls}; do
    echo "downloading rpm from: $url"
    curl -L ${url} -O . >/dev/null 2>&1
done

cd ..

