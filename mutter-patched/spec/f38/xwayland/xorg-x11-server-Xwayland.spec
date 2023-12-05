%define _disable_source_fetch 0
%global toolchain clang
%global pkgname xwayland
%global toolchain clang

%global default_font_path "catalogue:/etc/X11/fontpath.d,built-ins"

Summary:   Xwayland
Name:      xorg-x11-server-Xwayland
Version:   23.1.2
Release:   10%{?dist}.clang

URL:       http://www.x.org
Source0:   https://www.x.org/pub/individual/xserver/%{pkgname}-%{version}.tar.xz

License:   MIT

Requires: xorg-x11-server-common
Requires: libEGL
Requires: libepoxy >= 1.5.5

BuildRequires: gcc
BuildRequires: clang
BuildRequires: llvm
BuildRequires: lld
BuildRequires: git-core
BuildRequires: meson

BuildRequires: wayland-devel
BuildRequires: pkgconfig(wayland-client) >= 1.18.0
BuildRequires: pkgconfig(wayland-protocols)
BuildRequires: pkgconfig(wayland-eglstream-protocols)

BuildRequires: pkgconfig(epoxy) >= 1.5.5
BuildRequires: pkgconfig(fontenc)
BuildRequires: pkgconfig(libdrm) >= 2.4.0
BuildRequires: pkgconfig(libssl)
BuildRequires: pkgconfig(libtirpc)
BuildRequires: pkgconfig(pixman-1)
BuildRequires: pkgconfig(x11)
BuildRequires: pkgconfig(xau)
BuildRequires: pkgconfig(xdmcp)
BuildRequires: pkgconfig(xext)
BuildRequires: pkgconfig(xfixes)
BuildRequires: pkgconfig(xfont2)
BuildRequires: pkgconfig(xi)
BuildRequires: pkgconfig(xinerama)
BuildRequires: pkgconfig(xkbfile)
BuildRequires: pkgconfig(xmu)
BuildRequires: pkgconfig(xorg-macros) >= 1.17
BuildRequires: pkgconfig(xpm)
BuildRequires: pkgconfig(xrender)
BuildRequires: pkgconfig(xres)
BuildRequires: pkgconfig(xshmfence) >= 1.1
BuildRequires: pkgconfig(xtrans) >= 1.3.2
BuildRequires: pkgconfig(xtst)
BuildRequires: pkgconfig(xv)
BuildRequires: pkgconfig(libxcvt)
BuildRequires: xorg-x11-proto-devel >= 7.7-10

BuildRequires: mesa-libGL-devel >= 9.2
BuildRequires: mesa-libEGL-devel
BuildRequires: mesa-libgbm-devel

BuildRequires: audit-libs-devel
BuildRequires: libselinux-devel >= 2.0.86-1

# libunwind is Exclusive for the following arches
%ifarch aarch64 %{arm} hppa ia64 mips ppc ppc64 %{ix86} x86_64
%if !0%{?rhel}
BuildRequires: libunwind-devel
%endif
%endif

BuildRequires: pkgconfig(xcb-aux)
BuildRequires: pkgconfig(xcb-image)
BuildRequires: pkgconfig(xcb-icccm)
BuildRequires: pkgconfig(xcb-keysyms)
BuildRequires: pkgconfig(xcb-renderutil)

%description
Xwayland is an X server for running X clients under Wayland.

%package devel
Summary: Development package
Requires: pkgconfig

%description devel
The development package provides the developmental files which are
necessary for developing Wayland compositors using Xwayland.

%prep
%autosetup -N -S git_am -n %{pkgname}-%{version}


%build
%meson \
        -Dxwayland_eglstream=true \
        -Ddefault_font_path=%{default_font_path} \
        -Dbuilder_string="Build ID: %{name} %{version}-%{release}" \
        -Dxkb_output_dir=%{_localstatedir}/lib/xkb \
        -Dxcsecurity=true \
        -Dglamor=true \
        -Ddri3=true

%meson_build

%install
%meson_install

# Remove unwanted files/dirs
rm $RPM_BUILD_ROOT%{_mandir}/man1/Xserver.1*
rm -Rf $RPM_BUILD_ROOT%{_libdir}/xorg
rm -Rf $RPM_BUILD_ROOT%{_includedir}/xorg
rm -Rf $RPM_BUILD_ROOT%{_datadir}/aclocal
rm -Rf $RPM_BUILD_ROOT%{_localstatedir}/lib/xkb

%files
%{_bindir}/Xwayland
%{_mandir}/man1/Xwayland.1*
%{_datadir}/applications/org.freedesktop.Xwayland.desktop

%files devel
%{_libdir}/pkgconfig/xwayland.pc