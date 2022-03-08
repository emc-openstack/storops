%if 0%{?fedora}
%global with_python3 1
%endif

%global pypi_name storops

# Uncomment below line to publish pre-release package
# %%global pre_release dev.1

Name:           python-%{pypi_name}
Version:        1.2.11
Release:        %{?pre_release:0.%{pre_release}}%{!?pre_release:1}%{?dist}
Summary:        Library for managing Unity/VNX systems.

License:        ASL 2.0
URL:            https://pypi.python.org/pypi/storops/
Source0:        https://github.com/emc-openstack/%{pypi_name}/archive/v%{version}/%{pypi_name}-v%{version}%{?pre_release:-%{pre_release}}.tar.gz
BuildArch:      noarch

%description
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.


%package -n python2-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python2-%{pypi_name}}

Requires:       python-bitmath >= 1.3.0
Requires:       python-cachez >= 0.1.2
Requires:       python-dateutil >= 2.4.2
Requires:       python-enum34
Requires:       python-persist-queue >= 0.2.3
Requires:       python-requests >= 2.8.1
Requires:       python-retryz >= 0.1.8
Requires:       python-six >= 1.9.0
Requires:       PyYAML

BuildRequires:  python2-devel
BuildRequires:  python-bitmath >= 1.3.0
BuildRequires:  python-cachez >= 0.1.2
BuildRequires:  python-dateutil >= 2.4.2
BuildRequires:  python-ddt
BuildRequires:  python-enum34
BuildRequires:  python-fasteners
BuildRequires:  python-hamcrest
BuildRequires:  python-mock
BuildRequires:  python-persist-queue >= 0.2.3
BuildRequires:  python-pytest
BuildRequires:  python-pytest-xdist
BuildRequires:  python-requests >= 2.8.1
BuildRequires:  python-retryz >= 0.1.8
BuildRequires:  python-six >= 1.9.0
BuildRequires:  python-setuptools
BuildRequires:  python-xmltodict
BuildRequires:  PyYAML


%description -n python2-%{pypi_name}
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.


%if 0%{?with_python3}
%package -n python3-%{pypi_name}
Summary:        %{summary}
%{?python_provide:%python_provide python3-%{pypi_name}}

Requires:       python3-bitmath >= 1.3.0
Requires:       python3-cachez >= 0.1.2
Requires:       python3-dateutil >= 2.4.2
Requires:       python3-persist-queue >= 0.2.3
Requires:       python3-requests >= 2.8.1
Requires:       python3-retryz >= 0.1.8
Requires:       python3-six >= 1.9.0
Requires:       python3-PyYAML

BuildRequires:  python3-devel
BuildRequires:  python3-bitmath >= 1.3.0
BuildRequires:  python3-cachez >= 0.1.2
BuildRequires:  python3-dateutil >= 2.4.2
BuildRequires:  python3-ddt
BuildRequires:  python3-fasteners
BuildRequires:  python3-hamcrest
BuildRequires:  python3-mock
BuildRequires:  python3-persist-queue >= 0.2.3
BuildRequires:  python3-pytest
BuildRequires:  python3-pytest-xdist
BuildRequires:  python3-requests >= 2.8.1
BuildRequires:  python3-retryz >= 0.1.8
BuildRequires:  python3-six >= 1.9.0
BuildRequires:  python3-xmltodict
BuildRequires:  python3-PyYAML

%description -n python3-%{pypi_name}
Library for managing Unity/VNX systems. Please refer to https://github.com/emc-openstack/storops for more details.

%endif


%prep
%setup -q -n %{pypi_name}-%{version}%{?pre_release:-%{pre_release}}


%build
%py2_build

%if 0%{?with_python3}
%py3_build
%endif


%install
%py2_install

%if 0%{?with_python3}
%py3_install
%endif


%files -n python2-%{pypi_name}
%license LICENSE.txt
%doc README.rst
%{python2_sitelib}/storops*
%exclude %{python2_sitelib}/storops_comptest*
%exclude %{python2_sitelib}/storops_test*

%if 0%{?with_python3}
%files -n python3-%{pypi_name}
%license LICENSE.txt
%doc README.rst
%{python3_sitelib}/storops*
%exclude %{python3_sitelib}/storops_comptest*
%exclude %{python3_sitelib}/storops_test*
%endif


%changelog
* Tue Mar 8 2022 Yong Huang <yong.huang@dell.com> - 1.2.11-1
- Release v1.2.11: https://github.com/emc-openstack/storops/releases/tag/v1.2.11

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

* Thu Dec 28 2017 Ryan Liang <ryan.liang@dell.com> - 0.5.6-0.dev.1
- Release v0.5.6-dev.1: https://github.com/emc-openstack/storops/releases/tag/r0.5.6-dev.1

* Fri Nov 17 2017 Ryan Liang <ryan.liang@dell.com> - 0.5.5-1
- Release v0.5.5: https://github.com/emc-openstack/storops/releases/tag/r0.5.5

* Wed Jun 28 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.15-1
- Release v0.4.15: https://github.com/emc-openstack/storops/releases/tag/r0.4.15

* Thu Jun 8 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.14-1
- Release v0.4.14: https://github.com/emc-openstack/storops/releases/tag/r0.4.14
