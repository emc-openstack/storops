%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%if 0%{?fedora}
%global with_python3 1
%endif

%define debug_package %{nil}
%global pypi_name storops

Name:           python-%{pypi_name}-vnx
Version:        1.2.10
Release:        1%{?dist}
Summary:        Library for managing Unity/VNX systems.

License:        ASL 2.0
URL:            https://pypi.python.org/pypi/storops/
Source0:        https://github.com/emc-openstack/%{pypi_name}/archive/v%{version}/%{pypi_name}-v%{version}.tar.gz

%description
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.


%package -n python2-%{pypi_name}-vnx
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}-vnx}

Requires:       python2-storops == %{version}
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

Requires:       python3-storops == %{version}
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
* Fri May 28 2021 Yong Huang <yong.huang@dell.com> - 1.2.10-1
- Release v1.2.10: https://github.com/emc-openstack/storops/releases/tag/v1.2.10

* Fri Apr 30 2021 Yong Huang <yong.huang@dell.com> - 1.2.9-1
- Release v1.2.9: https://github.com/emc-openstack/storops/releases/tag/v1.2.9

* Tue Nov 24 2020 Yong Huang <yong.huang@dell.com> - 1.2.8-1
- Release v1.2.8: https://github.com/emc-openstack/storops/releases/tag/v1.2.8

* Tue Sep 2 2020 Ryan Liang <ryan.liang@dell.com> - 1.2.7-1
- Release v1.2.7: https://github.com/emc-openstack/storops/releases/tag/v1.2.7

* Tue Jul 28 2020 Ryan Liang <ryan.liang@dell.com> - 1.2.6-1
- Release v1.2.6: https://github.com/emc-openstack/storops/releases/tag/v1.2.6

* Tue May 26 2020 Ryan Liang <ryan.liang@dell.com> - 1.2.5-1
- Release v1.2.5: https://github.com/emc-openstack/storops/releases/tag/v1.2.5

* Wed Apr 1 2020 Ryan Liang <ryan.liang@dell.com> - 1.2.4-1
- Release v1.2.4: https://github.com/emc-openstack/storops/releases/tag/v1.2.4

* Mon Jan 13 2020 Ryan Liang <ryan.liang@dell.com> - 1.2.3-1
- Release v1.2.3: https://github.com/emc-openstack/storops/releases/tag/v1.2.3

* Thu Nov 7 2019 Ryan Liang <ryan.liang@dell.com> - 1.2.2-1
- Release v1.2.2: https://github.com/emc-openstack/storops/releases/tag/r1.2.2

* Mon Aug 12 2019 Ryan Liang <ryan.liang@dell.com> - 1.2.1-1
- Release v1.2.1: https://github.com/emc-openstack/storops/releases/tag/r1.2.1

* Wed Jun 12 2019 Ryan Liang <ryan.liang@dell.com> - 1.2.0-1
- Release v1.2.0: https://github.com/emc-openstack/storops/releases/tag/r1.2.0

* Mon Feb 11 2019 Ryan Liang <ryan.liang@dell.com> - 1.1.0-1
- Release v1.1.0: https://github.com/emc-openstack/storops/releases/tag/r1.1.0

* Mon Nov 26 2018 Ryan Liang <ryan.liang@dell.com> - 1.0.1-1
- Release v1.0.1: https://github.com/emc-openstack/storops/releases/tag/r1.0.1

* Mon Nov 19 2018 Ryan Liang <ryan.liang@dell.com> - 1.0.0-1
- Release v1.0.0: https://github.com/emc-openstack/storops/releases/tag/r1.0.0

* Fri Oct 19 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.12-1
- Release v0.5.12: https://github.com/emc-openstack/storops/releases/tag/r0.5.12

* Fri Jul 20 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.11-1
- Release v0.5.11: https://github.com/emc-openstack/storops/releases/tag/r0.5.11

* Fri Jul 13 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.10-1
- Release v0.5.10: https://github.com/emc-openstack/storops/releases/tag/r0.5.10

* Mon Jun 11 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.9-1
- Release v0.5.9: https://github.com/emc-openstack/storops/releases/tag/r0.5.9

* Wed Apr 18 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.8-1
- Release v0.5.8: https://github.com/emc-openstack/storops/releases/tag/r0.5.8

* Thu Feb 1 2018 Ryan Liang <ryan.liang@dell.com> - 0.5.7-1
- Release v0.5.7: https://github.com/emc-openstack/storops/releases/tag/r0.5.7

* Fri Nov 17 2017 Ryan Liang <ryan.liang@dell.com> - 0.5.5-1
- Release v0.5.5: https://github.com/emc-openstack/storops/releases/tag/r0.5.5

* Wed Jun 28 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.15-1
- Release v0.4.15: https://github.com/emc-openstack/storops/releases/tag/r0.4.15

* Thu Jun 8 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.14-1
- Release v0.4.14: https://github.com/emc-openstack/storops/releases/tag/r0.4.14
