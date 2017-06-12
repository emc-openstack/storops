%{!?upstream_version: %global upstream_version %{version}%{?milestone}}
%if 0%{?fedora}
%global with_python3 1
%endif

%global pypi_name storops

Name:           python-%{pypi_name}
Version:        0.4.14
Release:        1%{?dist}
Summary:        Library for managing Unity/VNX systems.

License:        ASL 2.0
URL:            https://pypi.python.org/pypi/storops/
Source0:        https://github.com/emc-openstack/%{pypi_name}/archive/r%{version}/%{pypi_name}-%{version}.tar.gz
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
%setup -q -n %{pypi_name}-%{upstream_version}


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
* Thu Jun 8 2017 Ryan Liang <ryan.liang@dell.com> - 0.4.14-1
- Release v0.4.14: https://github.com/emc-openstack/storops/releases/tag/r0.4.14
