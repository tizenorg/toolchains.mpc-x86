%define __strip /bin/true
%define _build_name_fmt    %%{ARCH}/%%{NAME}-%%{VERSION}-%%{RELEASE}.%%{ARCH}.dontuse.rpm
# meta spec file for cross-chroot setup 
#
# Copyright (c) 2010  Jan-Simon Möller (jsmoeller@linuxfoundation.org)
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for this file, and modifications and additions to the
# file, is the same license as for the pristine package itself (unless the
# license for the pristine package is not an Open Source License, in which
# case the license is the MIT License). An "Open Source License" is a
# license that conforms to the Open Source Definition (Version 1.9)
# published by the Open Source Initiative.

## README
##
## In this file:
## 1) define name of original package (see oldname)
## 
## File binaries_to_prepare:
## 2) fill in the binaries which need to be available to the foreign chroot
##    e.g. /bin/bash   -  this will make a i586 bash available
##
## File libraries_to_prepare:
## 3) fill in the libraries which need special treatment by patchelf
##
## File special_script:
## 4) fill in the special scrit to call, if needed


#\/\/\/\/\/\/\/\/\/\/
### only changes here
#
# The original package name
%define oldname mpc
#
# The architectures this meta package is built on
%define myexclusive i586
#
### no changes needed below this line
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^



### no changes needed
#
# The new package name - convention is %oldname-x86
%define newname %{oldname}-x86
#
# The version of the original package is read from its rpm db info
%{expand:%%define newversion %(rpm -q --qf '[%{version}]' %oldname)}
#
# The license of the original package is read from its rpm db info
%{expand:%%define newlicense %(rpm -q --qf '[%{license}]' %oldname)}
#
# The group information of the original package
%{expand:%%define newgroup %(rpm -q --qf '[%{group}]' %oldname)}
#
# The summary of the original package
%{expand:%%define newsummary %(rpm -q --qf '[%{summary} - special version ]' %oldname)}
#
# New rpath to add to files on request
%define newrpath "/emul/ia32-linux/lib:/emul/ia32-linux/usr/lib"
#
# Some automatic checks for availability
# binaries_to_prepare
%define binaries_to_prepare %{expand:%(test -e %{_sourcedir}/binaries_to_prepare && echo 1 || echo 0)}
%define libraries_to_prepare %{expand:%(test -e %{_sourcedir}/libraries_to_prepare && echo 1 || echo 0)}
%define special_script %{expand:%(test -e %{_sourcedir}/special_script && echo 1 || echo 0)}
%define files_to_ignore %{expand:%(test -e %{_sourcedir}/files_to_ignore && echo 1 || echo 0)}
#
### no changes needed below this line

Name:          %newname
Version:       %newversion
Release:       1
AutoReqProv:   0
Provides:      %newname
BuildRequires: rpm grep tar patchelf sed
BuildRequires: %oldname
Requires:      %oldname
# no auto requirements - they're generated
License:       %newlicense
Group:         %newgroup
ExclusiveArch: %myexclusive
Summary:       %newsummary
BuildRoot:     %{_tmppath}/%{name}-%{version}-build
%if %binaries_to_prepare
Source10:      binaries_to_prepare
%endif
%if %libraries_to_prepare
Source20:      libraries_to_prepare
%endif
%if %special_script
Source30:      special_script
%endif
Source100:     baselibs.conf

%description
This is a meta-package providing %name.
It is not intended to be used in a normal System!
Original description:
%{expand:%(rpm -q --qf '[%{description}]' %oldname)}



%prep

%build

%install
set +x
mkdir -p %buildroot
rpm -ql %oldname > filestoinclude1
%if %files_to_ignore
for i in `cat %{_sourcedir}/files_to_ignore`; do
 echo "Ignoring file: $i"
 sed -e "s#^${i}.*##" -i filestoinclude1 
done
%endif
tar -T filestoinclude1 -cpf - | ( cd %buildroot && tar -xvpf - )
find %buildroot >  filestoinclude2
cat filestoinclude2 | sed -e "s#%{buildroot}##g" | uniq | sort > filestoinclude
%if %binaries_to_prepare
echo ""
echo "[ .oO Preparing binaries Oo. ]"
echo ""
mkdir %buildroot/%{_prefix}/share/applybinary/
set -x
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do
  echo "Processing binary: $binary"
#  deps=$(for i in `readelf -a "$binary" | grep "(NEEDED)" | sed -e "s/.*\[//g" -e "s/\].*//g" ` ; do rpm -q --whatprovides "$i" ; done)
  ldd /bin/rpm  | grep -v "ld-linux" | grep -v "linux-gate" |  sed -e "s#=.*##g" -e "s#^\t*##g"  > 1
  deps=$(for i in `cat 1` ; do rpm -q --whatprovides "$i" | grep -v "no package"; done)
  cleandeps=$(echo "$cleandeps" "$deps" | sort | uniq | sed -e "s/-[0-9].*//g")
  patchelf --debug --set-rpath %newrpath %buildroot/$binary
  patchelf --debug --set-interpreter /emul/ia32-linux/lib/ld-linux.so.2 %buildroot/$binary
  patchelf --print-rpath %buildroot/$binary
  patchelf --print-interpreter %buildroot/$binary
  echo "$binary" >> %buildroot/%{_prefix}/share/applybinary/%name
  echo ""
done
set +x
%endif
%if %libraries_to_prepare
echo ""
echo "[ .oO Preparing libraries Oo. ]"
echo ""
%endif
%if %special_script
echo ""
echo "[ .oO Executing special script Oo. ]"
echo ""
%endif

# lets start the shellquote nightmare ;)
shellquote()
{
    for arg; do
        arg=${arg//\\/\\\\}
#        arg=${arg//\$/\$}   # already needs quoting ;(
#        arg=${arg/\"/\\\"}  # dito
#        arg=${arg//\`/\`}   # dito
        arg=${arg//\\|/\|}
        arg=${arg//\\|/|}
        echo "$arg"
    done
}

echo "Creating baselibs_new.conf"
echo ""
rm -rRf /tmp/baselibs_new.conf || true
shellquote "%{name}" >> /tmp/baselibs_new.conf
shellquote "  targettype x86 block!" >> /tmp/baselibs_new.conf
shellquote "  targettype 32bit block!" >> /tmp/baselibs_new.conf
shellquote "  targettype arm autoreqprov off" >> /tmp/baselibs_new.conf
for i in $cleandeps ; do 
  shellquote "  targettype arm requires \"${i}-x86-arm\"" >> /tmp/baselibs_new.conf
done
shellquote "  targettype arm requires \"%{oldname}\" " >> /tmp/baselibs_new.conf
shellquote "  targettype arm prefix /emul/ia32-linux" >> /tmp/baselibs_new.conf
shellquote "  targettype arm extension -arm" >> /tmp/baselibs_new.conf
shellquote "  targettype arm +/" >> /tmp/baselibs_new.conf
shellquote "  targettype arm -%{_mandir}" >> /tmp/baselibs_new.conf
shellquote "  targettype arm -%{_docdir}" >> /tmp/baselibs_new.conf
shellquote "  targettype arm requires \"tizen-accelerator\"" >> /tmp/baselibs_new.conf
%if %binaries_to_prepare
#shellquote "  targettype arm post \"replacenative() {\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  echo \"Replacing \${myfile}. Backup is \${myfile}.orig-arm.\" \"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  mv \${myfile} \${myfile}.orig-arm ; ln -s <prefix>\${myfile} \${myfile} \"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"}\"" >> /tmp/baselibs_new.conf
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do
   shellquote "  targettype arm post \"  mv ${binary} ${binary}.orig-arm ; ln -s <prefix>${binary} ${binary} \"" >> /tmp/baselibs_new.conf
done
#shellquote "  targettype arm post \"toreplace=\`rpm -ql <name>-<extension> \| grep applybinary/<name>\`\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"if test x\${toreplace} != x ; then\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  files=\`cat \${toreplace}\`\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  for myfile in \${files}\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  do\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"    #only replace files and nothing else by accident\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"    #if test -f \${myfile}; then\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"      replacenative \$myfile\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"    #fi\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"  done\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm post \"fi\"" >> /tmp/baselibs_new.conf
shellquote " " >> /tmp/baselibs_new.conf
for binary in `cat %{_sourcedir}/binaries_to_prepare` ; do
  shellquote "  targettype arm preun \"  rm -f ${binary} ; mv ${binary}.orig-arm ${binary}\"" >> /tmp/baselibs_new.conf
done
#shellquote "  targettype arm preun \"toreplace=\`rpm -ql <name>-<extension> \| grep applybinary/<name>\`\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"if test x\${toreplace} != x ; then\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"  files=\`cat \${toreplace}\`\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"  for myfile in \${files}\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"   do\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"   #only replace files and nothing else by accident\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"    if test -f \${myfile}; then\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"      restorenative \$myfile\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"    fi\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"  done\"" >> /tmp/baselibs_new.conf
#shellquote "  targettype arm preun \"fi\"" >> /tmp/baselibs_new.conf
%endif

cat /tmp/baselibs_new.conf >> %{_sourcedir}/baselibs.conf


echo ""
echo ""
echo ""
echo "REQUIREMENTS:"
grep "requires" %{_sourcedir}/baselibs.conf
echo ""
echo ""
echo ""
sleep 2
set -x

%clean
rm -rf $RPM_BUILD_ROOT

%files -f filestoinclude
%defattr(-,root,root)
%if %binaries_to_prepare
/%{_prefix}/share/applybinary/%name
%endif
