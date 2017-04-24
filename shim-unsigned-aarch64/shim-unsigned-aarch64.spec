Name:           shim-unsigned-aarch64
Version:        0.9
Release:        1%{?dist}
Summary:        First-stage UEFI bootloader
ExclusiveArch:  aarch64
License:        BSD
URL:            https://github.com/rhinstaller/shim
Source0:        https://github.com/rhinstaller/shim/releases/download/%{version}/shim-%{version}.tar.bz2
Source1:        fedora-ca.cer
# currently here's what's in our dbx:
# grub2-efi-2.00-11.fc18.x86_64:
# grubx64.efi 6ac839881e73504047c06a1aac0c4763408ecb3642783c8acf77a2d393ea5cd7
# gcdx64.efi 065cd63bab696ad2f4732af9634d66f2c0d48f8a3134b8808750d378550be151
# grub2-efi-2.00-11.fc19.x86_64:
# grubx64.efi 49ece9a10a9403b32c8e0c892fd9afe24a974323c96f2cc3dd63608754bf9b45
# gcdx64.efi 99fcaa957786c155a92b40be9c981c4e4685b8c62b408cb0f6cb2df9c30b9978
# woops.
Source2:        dbx.esl
Source3:        rhtest.cer
Source4:        shim-find-debuginfo.sh

Patch0001:      0001-Typo-on-aarch64.patch

BuildRequires: git openssl-devel openssl
BuildRequires: pesign >= 0.106-1
BuildRequires: gnu-efi >= 3.0.3-3
BuildRequires: gnu-efi-devel >= 3.0.3-3

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
Provides: bundled(openssl) = 0.9.8zb

%global efiarch aa64
%global efidir %(eval echo $(grep ^ID= /etc/os-release | sed -e 's/^ID=//' -e 's/rhel/redhat/'))

%global debug_package %{nil}
%global __debug_package 1
%global _binaries_in_noarch_packages_terminate_build 0

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments.

%package -n shim-unsigned
Summary: First-stage UEFI bootloader (unsigned data)

%description -n shim-unsigned
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments.

%package -n shim-unsigned-aarch64-debuginfo
Obsoletes: shim-debuginfo < 0.9
Provides: shim-debuginfo = %{version}-%{release}
Summary: Debug information for package %{name}
Group: Development/Debug
AutoReqProv: 0
BuildArch: noarch

%description -n shim-unsigned-aarch64-debuginfo
This package provides debug information for package %{name}.
Debug information is useful when developing applications that use this
package or when debugging this package.

%prep
%setup -q -n shim-%{version}
git init
git config user.email "%{name}-owner@fedoraproject.org"
git config user.name "Fedora Ninjas"
git add .
git commit -a -q -m "%{version} baseline."
git am --ignore-whitespace %{patches} </dev/null
git config --unset user.email
git config --unset user.name

%build
MAKEFLAGS=""
if [ -f "%{SOURCE3}" ]; then
	MAKEFLAGS="VENDOR_CERT_FILE=%{SOURCE3} VENDOR_DBX_FILE=%{SOURCE2}"
fi
MAKEFLAGS="$MAKEFLAGS RELEASE=%{release}"
make 'DEFAULT_LOADER=\\\\grub%{efiarch}.efi' ${MAKEFLAGS} shim.efi MokManager.efi fallback.efi

%install
rm -rf $RPM_BUILD_ROOT
pesign -h -P -i shim.efi -h > shim.hash
install -D -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/shim/
install -D -d -m 0755 $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
install -m 0644 shim.hash $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/shim.hash
for x in shim fallback MokManager ; do
	install -m 0644 $x.efi $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
	install -m 0644 $x.so $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/
done

%global __debug_install_post						\
	bash %{SOURCE4}							\\\
		%{?_missing_build_ids_terminate_build:--strict-build-id}\\\
		%{?_find_debuginfo_opts} "%{_builddir}/%{?buildsubdir}"	\
	rm -f $RPM_BUILD_ROOT%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.so		\
	%{nil}

install -D -d -m 0755  $RPM_BUILD_ROOT/usr/src/debug/
pushd $RPM_BUILD_ROOT/usr/src/debug/
tar xf %{SOURCE0}
popd

%files -n shim-unsigned
%license COPYRIGHT
%dir %{_datadir}/shim
%dir %{_datadir}/shim/%{efiarch}-%{version}-%{release}/
%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.efi
%{_datadir}/shim/%{efiarch}-%{version}-%{release}/*.hash

%files -n shim-unsigned-aarch64-debuginfo -f debugfiles.list

%changelog
* Thu May 12 2016 Peter Jones <pjones@redhat.com> - - 0.9-1
- Initial split up of -aarch64
