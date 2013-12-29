#
# spec file for package dkms
#
# Copyright (c) 2013 SUSE LINUX Products GmbH, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

# Please submit bugfixes or comments via http://bugs.opensuse.org/



Summary: Dynamic Kernel Module Support Framework
Name: dkms
Version: 2.2.0.3
Release: 8.1
License: GPL-2.0+
Vendor: The Bumblebee Project
Group: System/Kernel
BuildArch: noarch
Requires: sed gawk findutils modutils tar cpio gzip grep mktemp
Requires: bash > 1.99
# because Mandriva calls this package dkms-minimal
Provides: dkms-minimal = %{version}
URL: http://linux.dell.com/dkms
Source0: http://linux.dell.com/dkms/permalink/dkms-%{version}.tar.bz2
Source100: %{name}.changes
Source101: %{name}.rpmlintrc
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}
%if 0%{?suse_version}
Patch0: %{name}-compat_suse_init_script.diff
Requires: kernel-devel
%endif
%if 0%{?fedora}
Requires: kernel-devel
%endif

%description
This package contains the framework for the Dynamic
Kernel Module Support (DKMS) method for installing
module RPMS as originally developed by Dell.

%prep
%setup -q
%if 0%{?suse_version}
%patch0 -p1
%endif


%build

%triggerpostun -- %{name} < 1.90.00-1
for dir in `find %{_localstatedir}/%{name} -type d -maxdepth 1 -mindepth 1`; do
        mv -f $dir %{_localstatedir}/lib/%{name}
done
[ -e %{_sysconfdir}/dkms_framework.conf ] && ! [ -e %{_sysconfdir}/%{name}/framework.conf ] && mkdir %{_sysconfdir}/%{name} && cp -a %{_sysconfdir}/dkms_framework.conf %{_sysconfdir}/%{name}/framework.conf
arch_used=""
[ `uname -m` == "x86_64" ] && [ `cat /proc/cpuinfo | grep -c "Intel"` -gt 0 ] && arch_used="ia32e" || arch_used=`uname -m`
echo ""
echo "ALERT! ALERT! ALERT!"
echo ""
echo "You are using a version of DKMS which does not support multiple system"
echo "architectures.  Your DKMS tree will now be modified to add this support."
echo ""
echo "The upgrade will assume all built modules are for arch: $arch_used"
current_kernel=`uname -r`
dkms_tree="%{_localstatedir}/lib/%{name}"
source_tree="%{_prefix}/src"
tmp_location="/tmp"
dkms_frameworkconf="%{_sysconfdir}/%{name}/framework.conf"
. $dkms_frameworkconf 2>/dev/null
echo ""
echo "Fixing directories."
for directory in `find $dkms_tree -type d -name "module" -mindepth 3 -maxdepth 4`; do
        dir_to_fix=`echo $directory | sed 's#/module$##'`
        echo "Creating $dir_to_fix/$arch_used..."
        mkdir $dir_to_fix/$arch_used
        mv -f $dir_to_fix/* $dir_to_fix/$arch_used 2>/dev/null
done
echo ""
echo "Fixing symlinks."
for symlink in `find $dkms_tree -type l -name "kernel*" -mindepth 2 -maxdepth 2`; do
        symlink_kernelname=`echo $symlink | sed 's#.*/kernel-##'`
        dir_of_symlink=`echo $symlink | sed 's#/kernel-.*$##'`
        cd $dir_of_symlink
        read_link="$symlink"
        while [ -L "$read_link" ]; do
                read_link=`ls -l $read_link | sed 's/.*-> //'`
        done
        if [ `echo $read_link | sed 's#/# #g' | wc -w | awk {'print $1'}` -lt 3 ]; then
                echo "Updating $symlink..."
                ln -sf $read_link/$arch_used kernel-$symlink_kernelname-$arch_used
                rm -f $symlink
        fi
        cd -
done
echo ""

%install
make install-redhat DESTDIR=$RPM_BUILD_ROOT \
    SBIN=$RPM_BUILD_ROOT%{_sbindir} \
    VAR=$RPM_BUILD_ROOT%{_localstatedir}/lib/%{name} \
    MAN=$RPM_BUILD_ROOT%{_mandir}/man8 \
    ETC=$RPM_BUILD_ROOT%{_sysconfdir}/%{name} \
    BASHDIR=$RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d \
    LIBDIR=$RPM_BUILD_ROOT%{_prefix}/lib/%{name}

%if 0%{?suse_version}
# create rcdkms_autoinstaller symlink for openSUSE
%if 0%{?suse_version} < 1130
%define _initddir       /etc/init.d
%endif
mkdir -p $RPM_BUILD_ROOT/%{_initddir}
mv $RPM_BUILD_ROOT/etc/rc.d/init.d/dkms_autoinstaller $RPM_BUILD_ROOT/%{_initddir}/dkms_autoinstaller
ln -sf %{_initddir}/dkms_autoinstaller $RPM_BUILD_ROOT/usr/sbin/rcdkms_autoinstaller
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_sbindir}/%{name}
%if 0%{?suse_version}
%{_sbindir}/rcdkms_autoinstaller
%endif
%{_localstatedir}/lib/%{name}
%{_prefix}/lib/%{name}
%{_mandir}/*/*
%config(noreplace) %{_sysconfdir}/%{name}
%doc sample.spec sample.conf AUTHORS COPYING README.dkms
%doc sample-suse-9-mkkmp.spec sample-suse-10-mkkmp.spec
# these dirs are for plugins - owned by other packages
%{_initddir}/dkms_autoinstaller
%{_sysconfdir}/kernel/postinst.d/%{name}
%{_sysconfdir}/kernel/prerm.d/%{name}
%config %{_sysconfdir}/bash_completion.d/%{name}

%if 0%{?suse_version}
# suse doesnt yet support /etc/kernel/{prerm.d,postinst.d}, but will fail build
# with unowned dirs if we dont own them ourselves
# when opensuse *does* add this support, we will need to BuildRequires kernel
%dir %{_sysconfdir}/kernel
%dir %{_sysconfdir}/kernel/postinst.d
%dir %{_sysconfdir}/kernel/prerm.d
%endif


%post
[ -e /sbin/dkms ] && mv -f /sbin/dkms /sbin/dkms.old 2>/dev/null
# enable on initial install
[ $1 -lt 2 ] && /sbin/chkconfig dkms_autoinstaller on ||:
# make it more secure
if [ ! -d %{_tmppath}/dkms ] ;
then
  mkdir -p %{_tmppath}/dkms
  chmod 700 %{_tmppath}/dkms
fi
sed -i -e 's,# tmp_location="/tmp",tmp_location="%{_tmppath}/dkms",' %{_sysconfdir}/dkms/framework.conf

%postun
%insserv_cleanup
%restart_on_update

%preun
# remove on uninstall
[ $1 -lt 1 ] && ( /sbin/chkconfig dkms_autoinstaller off ; rm -rf %{_tmppath}/dkms ) ||:
%stop_on_removal

%changelog
* Wed Jul 24 2013 bumblebee.obs@gmail.com - 2.2.0.3
- security update
- changed default tmp directory to /var/tmp/dkms
- make /var/tmp/dkms directory only accessible by root
* Thu Dec 15 2011 bumblebee.obs@gmail.com - 2.2.0.3
- updated to 2.2.0.3
* Tue Nov  1 2011 bumblebee.obs@gmail.com - 2.2.0.2
- updated to 2.2.0.2
* Sat Oct 22 2011 bumblebee.obs@gmail.com - 2.1.1.2
- copy from packman repository
* Sat Oct  9 2010 packman@links2linux.de - 2.1.1.2
- moved to packman repository
* Tue Feb 23 2010 AxelKoellhofer@web.de - 2.1.1.2
- updated to 2.1.1.2
- obsolete patch for init script removed (fixed upstream)
* Fri Feb  5 2010 AxelKoellhofer@web.de - 2.1.1.1
- updated to 2.1.1.1
- fixed init script dkms_autoinstaller (line 142, if - then -  elif
  without a command to be executed after the if statement)
- RPM group switched to "Sytstem/Kernel"
- added PreReqs for coreutils, /bin/sed and /usr/bin/grep on openSUSE =< 11.0
