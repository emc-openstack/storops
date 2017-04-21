Name: storops_os
Version: 0.4.12
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

cp %{getenv:PWD}/requirements.txt $RPM_BUILD_ROOT/tmp/storops
pip download -r $RPM_BUILD_ROOT/tmp/storops/requirements.txt -d $RPM_BUILD_ROOT/tmp/storops
pip download -d $RPM_BUILD_ROOT/tmp/storops --no-deps storops

%post
echo Installing storops and dependencies.
pip install --no-index --find-links file:///tmp/storops storops

%clean
rm -rf "$RPM_BUILD_ROOT/tmp"

%files
%defattr (-,root,root)
/tmp/storops/*


%changelog
* Fri Apr 21 2017 Denny Zhao
- 0.4.12 for storops 0.4.12 and it's dependencies.

* Fri Mar 23 2017 Denny Zhao
- 0.4.10 for storops 0.4.10 and it's dependencies.

* Fri Mar 17 2017 Denny Zhao
- 0.4.8 for storops 0.4.8 and it's dependencies.

* Sat Feb 04 2017 Cedric Zhuang
- 0.4.5 for storops 0.4.5 and it's dependencies.

