#!/bin/sh
# Build GnuCOBOL 3.2 from the release tarball into $PREFIX (default
# $HOME/gnucobol-3.2). The tarball is verified against the pinned SHA-256
# below before it is unpacked; a mismatch stops the build.
#
# Provenance of the checksum (see docs/findings.md): computed from the
# SourceForge download of gnucobol-3.2.tar.xz; its SHA-1 and MD5 match the
# values SourceForge publishes for that file.
set -eu

SHA256=3bb48af46ced4779facf41fdc2ee60e4ccb86eaa99d010b36685315df39c2ee2
PREFIX=${PREFIX:-$HOME/gnucobol-3.2}
WORK=${WORK:-$(mktemp -d)}

cd "$WORK"
for url in \
    https://ftp.gnu.org/gnu/gnucobol/gnucobol-3.2.tar.xz \
    https://sourceforge.net/projects/gnucobol/files/gnucobol/3.2/gnucobol-3.2.tar.xz/download
do
    if curl -fsSL --retry 3 -o gnucobol-3.2.tar.xz "$url"; then
        echo "downloaded from $url"
        break
    fi
done
echo "$SHA256  gnucobol-3.2.tar.xz" | sha256sum -c -

tar xf gnucobol-3.2.tar.xz
cd gnucobol-3.2
./configure --prefix="$PREFIX" --without-db --without-xml2 --without-json \
    --without-curses --disable-nls
make -j"$(nproc)"
make install
"$PREFIX/bin/cobc" --version | head -1
