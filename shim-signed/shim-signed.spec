Name:           shim-signed
Version:        0.8
Release:        10
Summary:        First-stage UEFI bootloader
Requires:	dbxtool >= 0.6-3
Provides:	shim = %{version}-%{release}
%ifarch aarch64
%define unsignedver 0.9-1.fc24
%define unsigneddir %{_datadir}/shim/aa64-%{unsignedver}/
%endif
%ifarch x86_64
%define unsignedver 0.8-1.fc22
%define unsigneddir %{_datadir}/shim/
%endif
%ifarch %{ix86}
%define unsignedver 0.9-1.fc24
%define unsigneddir %{_datadir}/shim/ia32-%{unsignedver}/
%endif

License:        BSD
URL:            https://github.com/rhinstaller/shim

# keep these two lists of sources synched up arch-wise.  That is 0 and 10
# match, 1 and 11 match, ...
Source0:	BOOTX64.CSV
Source1:	BOOTAA64.CSV
Source2:	BOOTIA32.CSV

Source10:	shimx64.efi
Source11:	shimaa64.efi
Source12:	shimia32.efi

%ifarch x86_64
%global efiarch x64
%global bootarch X64
%global shimsrc %{SOURCE10}
%global bootcsv %{SOURCE0}
%endif

%ifarch aarch64
%global efiarch aa64
%global bootarch AA64
%global shimsrc %{SOURCE11}
%global bootcsv %{SOURCE1}
%endif

%ifarch %{ix86}
%global efiarch ia32
%global bootarch IA32
%global shimsrc %{SOURCE12}
%global bootcsv %{SOURCE2}
%endif

BuildRequires: shim-unsigned = %{unsignedver}
BuildRequires: pesign >= 0.100-1%{dist}

# Shim uses OpenSSL, but cannot use the system copy as the UEFI ABI is not
# compatible with SysV (there's no red zone under UEFI) and there isn't a
# POSIX-style C library.
# BuildRequires: OpenSSL
%ifarch x86_64
Provides: bundled(openssl) = 0.9.8zb
%endif
%ifnarch x86_64
Provides: bundled(openssl) = 1.0.2d
%endif

# Shim is only required on platforms implementing the UEFI secure boot
# protocol. The only one of those we currently wish to support is 64-bit x86.
# Adding further platforms will require adding appropriate relocation code.
ExclusiveArch: x86_64 aarch64

%global debug_package %{nil}

# Figure out the right file path to use
%if 0%{?rhel}
%global efidir redhat
%endif
%if 0%{?fedora}
%global efidir fedora
%endif

%define ca_signed_arches x86_64 %{ix86}
%define rh_signed_arches x86_64 %{ix86} aarch64

%description
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%package -n shim
Summary: First-stage UEFI bootloader
Requires: mokutil >= 1:0.2.0-1
Provides: shim-signed = %{version}-%{release}
Obsoletes: shim-signed < %{version}-%{release}

%description -n shim
Initial UEFI bootloader that handles chaining to a trusted full bootloader
under secure boot environments. This package contains the version signed by
the UEFI signing service.

%prep
cd %{_builddir}
rm -rf shim-signed-%{version}
mkdir shim-signed-%{version}

%build
%define vendor_token_str %{expand:%%{nil}%%{?vendor_token_name:-t "%{vendor_token_name}"}}
%define vendor_cert_str %{expand:%%{!?vendor_cert_nickname:-c "Red Hat Test Certificate"}%%{?vendor_cert_nickname:-c "%%{vendor_cert_nickname}"}}

cd shim-signed-%{version}
%ifarch %{ca_signed_arches}
pesign -i %{shimsrc} -h -P > shim.hash
if ! cmp shim.hash %{unsigneddir}/shim.hash ; then
	echo Invalid signature\! > /dev/stderr
	exit 1
fi
%endif
cp %{shimsrc} shim.efi
cp %{unsigneddir}/shim.efi shim-unsigned.efi

%ifarch %{rh_signed_arches}
%pesign -s -i shim-unsigned.efi -o shim-%{efidir}.efi
%ifnarch %{ca_signed_arches}
cp shim-%{efidir}.efi shim.efi
%endif
%endif

cp %{unsigneddir}/MokManager.efi MokManager-unsigned.efi
cp %{unsigneddir}/fallback.efi fallback-unsigned.efi
%pesign -s -i MokManager-unsigned.efi -o MokManager.efi
%pesign -s -i fallback-unsigned.efi -o fallback.efi
rm -vf MokManager-unsigned.efi \
	fallback-unsigned.efi \
	shim-unsigned.efi

%install
rm -rf $RPM_BUILD_ROOT
cd shim-signed-%{version}
install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/
install -m 0644 shim.efi \
	$RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim.efi
install -m 0644 shim-%{efidir}.efi \
	$RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/shim-%{efidir}.efi
install -m 0644 MokManager.efi \
	$RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/MokManager.efi
%ifarch x86_64
install -m 0644 %{bootcsv} $RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT.CSV
%endif
install -m 0644 %{bootcsv} \
	$RPM_BUILD_ROOT/boot/efi/EFI/%{efidir}/BOOT.CSV

install -D -d -m 0755 $RPM_BUILD_ROOT/boot/efi/EFI/BOOT/
install -m 0644 shim.efi \
	$RPM_BUILD_ROOT/boot/efi/EFI/BOOT/BOOT%{bootarch}.EFI
install -m 0644 fallback.efi \
	$RPM_BUILD_ROOT/boot/efi/EFI/BOOT/fallback.efi

%files -n shim
/boot/efi/EFI/%{efidir}/*.efi
/boot/efi/EFI/%{efidir}/BOOT*.CSV
/boot/efi/EFI/BOOT/*.efi
/boot/efi/EFI/BOOT/*.EFI

%changelog
* Mon Aug 15 2016 Peter Jones <pjones@redhat.com> - 0.8-10
- Rebuild to get the #1333888 fix into f25.
  Resolves: rhbz#1352646

* Tue May 17 2016 Peter Jones <pjones@redhat.com> - 0.8-9
- Move aarch64 to 0.9-1
  Resolves: rhbz#1333888

* Tue Feb 17 2015 Peter Jones <pjones@redhat.com> - 0.8-8
- Don't dual-sign shim-%{efidir}.efi either.
  Resolves: rhbz#1184765

* Tue Feb 17 2015 Peter Jones <pjones@redhat.com> - 0.8-8
- Require dbxtool

* Wed Dec 17 2014 Peter Jones <pjones@redhat.com> - 0.8-7
- Wrong -signed changes got built for aarch64 last time, for dumb reasons.
  Related: rhbz#1170289

* Fri Dec 05 2014 Peter Jones <pjones@redhat.com> - 0.8-6
- Rebuild once more so we can use a different -unsigned version on different
  arches (because we can't tag a newer build into aarch64 without an x86
  update to match.)
  Related: rhbz#1170289

* Wed Dec 03 2014 Peter Jones <pjones@redhat.com> - 0.8-5
- Rebuild for aarch64 path fixes
  Related: rhbz#1170289

* Thu Oct 30 2014 Peter Jones <pjones@redhat.com> - 0.8-2
- Remove the dist tag so people don't complain about what it says.

* Fri Oct 24 2014 Peter Jones <pjones@redhat.com> - 0.8-1
- Update to shim 0.8
  rhbz#1148230
  rhbz#1148231
  rhbz#1148232
- Handle building on aarch64 as well

* Fri Jul 18 2014 Peter Jones <pjones@redhat.com> - 0.7-2
- Don't do multi-signing; too many machines screw up verification.
  Resolves: rhbz#1049749

* Wed Nov 13 2013 Peter Jones <pjones@redhat.com> - 0.7-1
- Update to shim 0.7
  Resolves: rhbz#1023767

* Thu Oct 24 2013 Peter Jones <pjones@redhat.com> - 0.5-1
- Update to shim 0.5

* Thu Jun 20 2013 Peter Jones <pjones@redhat.com> - 0.4-1
- Provide a fallback for uninitialized Boot#### and BootOrder
  Resolves: rhbz#963359
- Move all signing from shim-unsigned to here
- properly compare our generated hash from shim-unsigned with the hash of
  the signed binary (as opposed to doing it manually)

* Fri May 31 2013 Peter Jones <pjones@redhat.com> - 0.2-4.4
- Re-sign to get alignments that match the new specification.
  Resolves: rhbz#963361

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.2-4.3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jan 02 2013 Peter Jones <pjones@redhat.com> - 0.2-3.3
- Add obsoletes and provides for earlier shim-signed packages, to cover
  the package update cases where previous versions were installed.
  Related: rhbz#888026

* Mon Dec 17 2012 Peter Jones <pjones@redhat.com> - 0.2-3.2
- Make the shim-unsigned dep be on the subpackage.

* Sun Dec 16 2012 Peter Jones <pjones@redhat.com> - 0.2-3.1
- Rebuild to provide "shim" package directly instead of just as a Provides:

* Sat Dec 15 2012 Peter Jones <pjones@redhat.com> - 0.2-3
- Also provide shim-fedora.efi, signed only by the fedora signer.
- Fix the fedora signature on the result to actually be correct.
- Update for shim-unsigned 0.2-3

* Mon Dec 03 2012 Peter Jones <pjones@redhat.com> - 0.2-2
- Initial build
