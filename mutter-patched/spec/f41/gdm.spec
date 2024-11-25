%global _hardened_build 1

%global toolchain clang

%define gtk3_version 2.99.2

%global tarball_version %%(echo %{version} | tr '~' '.')

Name:           gdm
Epoch:          1
Version:        47.0
Release:        10%{?dist}.clang
Summary:        The GNOME Display Manager

License:        GPL-2.0-or-later
URL:            https://wiki.gnome.org/Projects/GDM
Source0:        https://download.gnome.org/sources/gdm/47/gdm-%{tarball_version}.tar.xz
Source1:        org.gnome.login-screen.gschema.override

# moved here from pulseaudio-gdm-hooks-11.1-16
Source5:        https://raw.githubusercontent.com/TrixieUA/copr-trixieua/main/mutter-patched/patches/f41/gdm/default.pa-for-gdm

Source6:        https://raw.githubusercontent.com/TrixieUA/copr-trixieua/main/mutter-patched/patches/f41/gdm/gdm.sysusers

# Downstream patches
Patch:          https://raw.githubusercontent.com/TrixieUA/copr-trixieua/main/mutter-patched/patches/f41/gdm/0001-Honor-initial-setup-being-disabled-by-distro-install.patch
Patch:          https://raw.githubusercontent.com/TrixieUA/copr-trixieua/main/mutter-patched/patches/f41/gdm/0001-data-add-system-dconf-databases-to-gdm-profile.patch
Patch:          https://raw.githubusercontent.com/TrixieUA/copr-trixieua/main/mutter-patched/patches/f41/gdm/0001-Add-headless-session-files.patch

BuildRequires:  clang
BuildRequires:  dconf
BuildRequires:  desktop-file-utils
BuildRequires:  gettext-devel
BuildRequires:  libXdmcp-devel
BuildRequires:  git-core
BuildRequires:  meson
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(accountsservice) >= 0.6.3
BuildRequires:  pkgconfig(audit)
BuildRequires:  pkgconfig(check)
BuildRequires:  pkgconfig(gobject-introspection-1.0)
BuildRequires:  pkgconfig(gtk+-3.0) >= %{gtk3_version}
BuildRequires:  pkgconfig(gudev-1.0)
BuildRequires:  pkgconfig(iso-codes)
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(libcanberra-gtk3)
BuildRequires:  pkgconfig(libkeyutils)
BuildRequires:  pkgconfig(libselinux)
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(ply-boot-client)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(x11)
BuildRequires:  pkgconfig(xau)
BuildRequires:  systemd-rpm-macros
BuildRequires:  which
BuildRequires:  yelp-tools

Provides: service(graphical-login) = %{name}

Requires: accountsservice
Requires: dconf
# since we use it, and pam spams the log if the module is missing
Requires: gnome-keyring-pam
Requires: gnome-session
Requires: gnome-session-wayland-session
Requires: gnome-settings-daemon >= 3.27.90
Requires: gnome-shell
Requires: iso-codes
# We need 1.0.4-5 since it lets us use "localhost" in auth cookies
Requires: libXau >= 1.0.4-4
Requires: pam
Requires: /sbin/nologin
Requires: systemd >= 186
Requires: system-logos
Requires: python3-pam

# Until the greeter gets dynamic user support, it can't
# use a user bus
Requires: /usr/bin/dbus-run-session

%{?sysusers_requires_compat}

Provides: gdm-libs%{?_isa} = %{epoch}:%{version}-%{release}

%description
GDM, the GNOME Display Manager, handles authentication-related backend
functionality for logging in a user and unlocking the user's session after
it's been locked. GDM also provides functionality for initiating user-switching,
so more than one user can be logged in at the same time. It handles
graphical session registration with the system for both local and remote
sessions (in the latter case, via GNOME Remote Desktop and the RDP protocol).

%package devel
Summary: Development files for gdm
Requires: %{name}%{?_isa} = %{epoch}:%{version}-%{release}
Requires: gdm-pam-extensions-devel = %{epoch}:%{version}-%{release}

%description devel
The gdm-devel package contains headers and other
files needed to build custom greeters.

%package pam-extensions-devel
Summary: Macros for developing GDM extensions to PAM
Requires: pam-devel

%description pam-extensions-devel
The gdm-pam-extensions-devel package contains headers and other
files that are helpful to PAM modules wishing to support
GDM specific authentication features.

%prep
%autosetup -S git -p1 -n gdm-%{tarball_version}

%build
%meson -Dpam-prefix=%{_sysconfdir} \
       -Drun-dir=/run/gdm \
       -Ddefault-path=/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin \
       -Ddefault-pam-config=redhat \
       -Ddistro=redhat \
       -Dprofiling=true \
       -Dplymouth=enabled \
       -Dselinux=enabled\
       -Dwayland-support=true \
       -Dx11-support=true \
       -Dxdmcp=enabled

%meson_build


%install
mkdir -p %{buildroot}%{_sysconfdir}/gdm/Init
mkdir -p %{buildroot}%{_sysconfdir}/gdm/PreSession
mkdir -p %{buildroot}%{_sysconfdir}/gdm/PostSession

%meson_install

install -p -m644 -D %{SOURCE5} %{buildroot}%{_localstatedir}/lib/gdm/.config/pulse/default.pa
install -p -m644 -D %{SOURCE6} %{buildroot}%{_sysusersdir}/%{name}.conf

# add logo to shell greeter
cp -a %{SOURCE1} %{buildroot}%{_datadir}/glib-2.0/schemas

# docs go elsewhere
rm -rf %{buildroot}/%{_prefix}/doc

rm -f %{buildroot}/%{_udevrulesdir}/61-gdm.rules

# create log dir
mkdir -p %{buildroot}/var/log/gdm

(cd %{buildroot}%{_sysconfdir}/gdm; ln -sf ../X11/xinit/Xsession .)

mkdir -p %{buildroot}%{_datadir}/gdm/autostart/LoginWindow

mkdir -p %{buildroot}/run/gdm

mkdir -p %{buildroot}%{_sysconfdir}/dconf/db/gdm.d/locks

%find_lang gdm --with-gnome

%pre
%sysusers_create_compat %{SOURCE6}

%post
# if the user already has a config file, then migrate it to the new
# location; rpm will ensure that old file will be renamed

custom=/etc/gdm/custom.conf

if [ $1 -ge 2 ] ; then
    if [ -f /usr/share/gdm/config/gdm.conf-custom ]; then
        oldconffile=/usr/share/gdm/config/gdm.conf-custom
    elif [ -f /etc/X11/gdm/gdm.conf ]; then
        oldconffile=/etc/X11/gdm/gdm.conf
    fi

    # Comment out some entries from the custom config file that may
    # have changed locations in the update.  Also move various
    # elements to their new locations.

    [ -n "$oldconffile" ] && sed \
    -e 's@^command=/usr/X11R6/bin/X@#command=/usr/bin/Xorg@' \
    -e 's@^Xnest=/usr/X11R6/bin/Xnest@#Xnest=/usr/X11R6/bin/Xnest@' \
    -e 's@^BaseXsession=/etc/X11/xdm/Xsession@#BaseXsession=/etc/X11/xinit/Xsession@' \
    -e 's@^BaseXsession=/etc/X11/gdm/Xsession@#&@' \
    -e 's@^BaseXsession=/etc/gdm/Xsession@#&@' \
    -e 's@^Greeter=/usr/bin/gdmgreeter@#Greeter=/usr/libexec/gdmgreeter@' \
    -e 's@^RemoteGreeter=/usr/bin/gdmlogin@#RemoteGreeter=/usr/libexec/gdmlogin@' \
    -e 's@^GraphicalTheme=Bluecurve@#&@' \
    -e 's@^BackgroundColor=#20305a@#&@' \
    -e 's@^DefaultPath=/usr/local/bin:/usr/bin:/bin:/usr/X11R6/bin@#&@' \
    -e 's@^RootPath=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin:/usr/X11R6/bin@#&@' \
    -e 's@^HostImageDir=/usr/share/hosts/@#HostImageDir=/usr/share/pixmaps/faces/@' \
    -e 's@^LogDir=/var/log/gdm@#&@' \
    -e 's@^PostLoginScriptDir=/etc/X11/gdm/PostLogin@#&@' \
    -e 's@^PreLoginScriptDir=/etc/X11/gdm/PreLogin@#&@' \
    -e 's@^PreSessionScriptDir=/etc/X11/gdm/PreSession@#&@' \
    -e 's@^PostSessionScriptDir=/etc/X11/gdm/PostSession@#&@' \
    -e 's@^DisplayInitDir=/var/run/gdm.pid@#&@' \
    -e 's@^RebootCommand=/sbin/reboot;/sbin/shutdown -r now;/usr/sbin/shutdown -r now;/usr/bin/reboot@#&@' \
    -e 's@^HaltCommand=/sbin/poweroff;/sbin/shutdown -h now;/usr/sbin/shutdown -h now;/usr/bin/poweroff@#&@' \
    -e 's@^ServAuthDir=/var/gdm@#&@' \
    -e 's@^Greeter=/usr/bin/gdmlogin@Greeter=/usr/libexec/gdmlogin@' \
    -e 's@^RemoteGreeter=/usr/bin/gdmgreeter@RemoteGreeter=/usr/libexec/gdmgreeter@' \
    $oldconffile > $custom
fi

if [ $1 -ge 2 -a -f $custom ] && grep -q /etc/X11/gdm $custom ; then
   sed -i -e 's@/etc/X11/gdm@/etc/gdm@g' $custom
fi

%systemd_post gdm.service

%preun
%systemd_preun gdm.service

%postun
%systemd_postun gdm.service

%files -f gdm.lang
%doc AUTHORS NEWS README.md
%license COPYING
%dir %{_sysconfdir}/gdm
%config(noreplace) %{_sysconfdir}/gdm/custom.conf
%config %{_sysconfdir}/gdm/Init/*
%config %{_sysconfdir}/gdm/PostLogin/*
%config %{_sysconfdir}/gdm/PreSession/*
%config %{_sysconfdir}/gdm/PostSession/*
%config %{_sysconfdir}/pam.d/gdm-autologin
%config %{_sysconfdir}/pam.d/gdm-password
# not config files
%{_sysconfdir}/gdm/Xsession
%{_datadir}/gdm/gdm.schemas
%{_sysconfdir}/dbus-1/system.d/gdm.conf
%dir %{_sysconfdir}/gdm/Init
%dir %{_sysconfdir}/gdm/PreSession
%dir %{_sysconfdir}/gdm/PostSession
%dir %{_sysconfdir}/gdm/PostLogin
%dir %{_sysconfdir}/dconf/db/gdm.d
%dir %{_sysconfdir}/dconf/db/gdm.d/locks
%{_datadir}/glib-2.0/schemas/org.gnome.login-screen.gschema.xml
%{_datadir}/glib-2.0/schemas/org.gnome.login-screen.gschema.override
%{_libexecdir}/gdm-runtime-config
%{_libexecdir}/gdm-session-worker
%{_libexecdir}/gdm-wayland-session
%{_libexecdir}/gdm-headless-login-session
%{_sbindir}/gdm
%{_bindir}/gdmflexiserver
%{_bindir}/gdm-config
%dir %{_datadir}/dconf
%dir %{_datadir}/dconf/profile
%{_datadir}/dconf/profile/gdm
%dir %{_datadir}/gdm/greeter
%dir %{_datadir}/gdm/greeter/applications
%{_datadir}/gdm/greeter/applications/*
%dir %{_datadir}/gdm/greeter/autostart
%{_datadir}/gdm/greeter/autostart/*
%{_datadir}/gdm/greeter-dconf-defaults
%{_datadir}/gdm/locale.alias
%{_datadir}/gdm/gdb-cmd
%{_datadir}/gnome-session/sessions/gnome-login.session
%{_libdir}/girepository-1.0/Gdm-1.0.typelib
%{_libdir}/security/pam_gdm.so
%{_libdir}/libgdm*.so*
%{_libexecdir}/gdm-auth-config-redhat
%attr(0711, root, gdm) %dir %{_localstatedir}/log/gdm
%attr(1770, gdm, gdm) %dir %{_localstatedir}/lib/gdm
%attr(0700, gdm, gdm) %dir %{_localstatedir}/lib/gdm/.config
%attr(0700, gdm, gdm) %dir %{_localstatedir}/lib/gdm/.config/pulse
%attr(0600, gdm, gdm) %{_localstatedir}/lib/gdm/.config/pulse/default.pa
%attr(0711, root, gdm) %dir /run/gdm
%config %{_sysconfdir}/pam.d/gdm-smartcard
%config %{_sysconfdir}/pam.d/gdm-fingerprint
%{_sysconfdir}/pam.d/gdm-launch-environment
%{_unitdir}/gdm.service
%{_unitdir}/gnome-headless-session@.service
%dir %{_userunitdir}/gnome-session@gnome-login.target.d/
%{_userunitdir}/gnome-session@gnome-login.target.d/session.conf
%{_sysusersdir}/%{name}.conf
%{_libexecdir}/gdm-host-chooser
%{_libexecdir}/gdm-simple-chooser
%{_libexecdir}/gdm-x-session

%files devel
%dir %{_includedir}/gdm
%{_includedir}/gdm/*.h
%exclude %{_includedir}/gdm/gdm-pam-extensions.h
%exclude %{_includedir}/gdm/gdm-choice-list-pam-extension.h
%exclude %{_includedir}/gdm/gdm-custom-json-pam-extension.h
%exclude %{_includedir}/gdm/gdm-pam-extensions-common.h
%dir %{_datadir}/gir-1.0
%{_datadir}/gir-1.0/Gdm-1.0.gir
%{_libdir}/pkgconfig/gdm.pc

%files pam-extensions-devel
%{_includedir}/gdm/gdm-pam-extensions.h
%{_includedir}/gdm/gdm-choice-list-pam-extension.h
%{_includedir}/gdm/gdm-custom-json-pam-extension.h
%{_includedir}/gdm/gdm-pam-extensions-common.h
%{_libdir}/pkgconfig/gdm-pam-extensions.pc