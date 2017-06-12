%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%if 0%{?fedora}
%global with_python3 1
%endif

%define debug_package %{nil}
%global pypi_name storops

Name:           python-%{pypi_name}
Version:        0.4.14
Release:        1%{?dist}
Summary:        Library for managing Unity/VNX systems.

License:        ASL 2.0
URL:            https://pypi.python.org/pypi/storops/
Source0:        https://github.com/emc-openstack/%{pypi_name}/archive/r%{version}/%{pypi_name}-%{version}.tar.gz

%description
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.


%package -n python2-%{pypi_name}-vnx
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}-vnx}

Requires:       python2-storops
%ifarch %ix86
Requires:       NaviCLI-Linux-32-x86-en_US
%endif
%ifarch x86_64 amd64
Requires:       NaviCLI-Linux-64-x86-en_US
%endif

%description -n python2-%{pypi_name}-vnx
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.


%if 0%{?with_python3}
%package -n python3-%{pypi_name}-vnx
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}-vnx}

Requires:       python3-storops
%ifarch %ix86
Requires:       NaviCLI-Linux-32-x86-en_US
%endif
%ifarch x86_64 amd64
Requires:       NaviCLI-Linux-64-x86-en_US
%endif

%description -n python3-%{pypi_name}-vnx
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.

%endif


%prep
%setup -q -n %{pypi_name}-%{upstream_version}


%files -n python2-%{pypi_name}-vnx
%license LICENSE.txt
%doc README.rst

%if 0%{?with_python3}
%files -n python3-%{pypi_name}-vnx
%license LICENSE.txt
%doc README.rst
%endif


%changelog
* Thu Jun 8 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.14-1
- Release v0.4.14: https://github.com/emc-openstack/storops/releases/tag/r0.4.14
