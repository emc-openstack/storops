Name: storops_os
Version: 0.4.8
Release: 0
Vendor: Cedric Zhuang
Summary: Python API for VNX and Unity.
License: Apache Software License
BuildArch: noarch
Group: Development/Libraries
URL: https://github.com/emc-openstack/storops
Packager: cedric.zhuang@gmail.com
%description
RPM package of Storops for Openstack distribution.

%prep
%install
# create the folders
mkdir -p $RPM_BUILD_ROOT/tmp/storops

# put files into the pip folder
cp -a %{getenv:PWD}/pip_packs/* $RPM_BUILD_ROOT/tmp/storops

%post
echo Installing storops and dependencies.
pip install /tmp/storops/*

%clean
rm -rf "$RPM_BUILD_ROOT/tmp"

%files
%defattr (-,root,root)
/tmp/storops/*

%changelog
* Fri Mar 17 2017 Denny Zhao
- 0.4.8 for storops 0.4.8 and it's dependencies.

* Sat Feb 04 2017 Cedric Zhuang
- 0.4.5 for storops 0.4.5 and it's dependencies.

