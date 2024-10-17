Name:		foomatic-db-nonfree
Version:	20180615
Release:	1
Summary:	Foomatic database extensions
License:	GPLv2 and MIT
Group:		System/Servers
Url:		https://www.linuxprinting.org/
Source0:	http://www.linuxprinting.org/download/foomatic/%{name}-%{version}.tar.gz
# Perl script to clean up Manufacturer entries in the PPD files, so that
# drivers are sorted by the printer manufacturer in the graphical frontends
Source2:	cleanppd.pl.bz2
BuildArch:	noarch
BuildRequires:	cups
BuildRequires:	cups-common
BuildRequires:	foomatic-db-engine
Requires:	foomatic-db-engine

%description
Foomatic database extension with manufacturer-supplied PPD files
released under non-free licenses.

%prep

##### FOOMATIC

# Source trees for installation
%setup -q 

%build
# Makefile generation ("./make_configure" for CVS snapshots)
./make_configure
# Fix for lib64 architectures, avoid patch
perl -pi -e "s@/usr/lib/(cups|pdq|ppr)@%{_libdir}/\1@g" configure

# We do not compress the PPDs now, so that we can do a clean-up
%configure --disable-gzip-ppds

# "make" is not needed for this package, there is nothing to build

# Delete drivers with empty command line prototype, they would give
# unusable printer/driver combos.
#FOOMATICDB=`pwd` %{_sbindir}/foomatic-cleanupdrivers

# Correct recommended driver "gimp-print" or "gutenprint", must be 
# "gutenprint-ijs.5.0".
for f in db/source/printer/*.xml; do
	perl -p -i -e 's:<driver>(gimp-|guten)print</driver>:<driver>gutenprint-ijs.5.0</driver>:' $f
done

%install
# Do not use "make" macro, as parallelized build of Foomatic does not
# work.

# Install data files
make	PREFIX=%{_prefix} \
        DESTDIR=%{buildroot} \
        install

# Uncompress Perl script for cleaning up the PPD files
bzcat %{SOURCE2} > ./cleanppd.pl
chmod a+rx ./cleanppd.pl

# Do the clean-up
find %{buildroot}%{_datadir}/foomatic/db/source/PPD -name "*.ppd" -exec ./cleanppd.pl '{}' \;

# Remove PPDs which are not Adobe-compliant and therefore not working with
# CUPS 1.1.20 or newer
for ppd in `find %{buildroot}%{_datadir}/foomatic/db/source/PPD -name "*.ppd.gz"`
do
	cupstestppd -q $ppd || (
		rm -f $ppd && \
		echo "$ppd not Adobe-compliant. Deleted." && \
		echo $ppd >> deletedppds-%{name}-%{version}-%{release}.txt
	)
done

##### GENERAL STUFF

# Correct permissions
for f in %{buildroot}%{_datadir}/foomatic/db/source/*/*.xml; do
  chmod a-x $f
done

##### SCRIPTS

# Restart the CUPS daemon when it is running, but do not start it when it
# is not running. The restart of the CUPS daemon updates the CUPS-internal
# PPD index

%post
/sbin/service cups condrestart > /dev/null 2>/dev/null || :

%postun
/sbin/service cups condrestart > /dev/null 2>/dev/null || :

%files
%{_datadir}/foomatic/db/source/driver/*.xml
%{_datadir}/foomatic/db/source/PPD/*
%{_libdir}/cups/backend/beh
%{_libdir}/cups/filter/foomatic-rip
