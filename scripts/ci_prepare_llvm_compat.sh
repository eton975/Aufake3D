#!/usr/bin/env bash
# Build the old libxml2 SONAME needed by LLVM 19.1.7's Linux LLD binary.
# Only Ubuntu 26.04 and 26.10 need it. Keep it private and OUTSIDE checkout.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo 'Usage: ci_prepare_llvm_compat.sh /absolute/runner-temp-directory' >&2
  exit 2
fi

if [[ ! -r /etc/os-release ]]; then
  echo 'FAIL: cannot authenticate the build OS' >&2
  exit 1
fi
# shellcheck disable=SC1091
source /etc/os-release
if [[ "$ID" != 'ubuntu' || ( "$VERSION_ID" != '26.04' && "$VERSION_ID" != '26.10' ) ]]; then
  echo "FAIL: this LLVM compatibility build is only for Ubuntu 26.04/26.10, found ${ID:-unknown} ${VERSION_ID:-unknown}" >&2
  exit 1
fi

: "${LLVM_PATH:?LLVM installer must set LLVM_PATH}"
: "${GITHUB_ENV:?GitHub Actions must provide GITHUB_ENV}"
if [[ ! -f "$LLVM_PATH/bin/lld-link" ]]; then
  echo 'FAIL: pinned LLVM lld-link is missing' >&2
  exit 1
fi

workdir="$1"
if [[ "$workdir" != /* ]]; then
  echo 'FAIL: compatibility build directory must be an absolute path' >&2
  exit 1
fi
if [[ -n "${GITHUB_WORKSPACE:-}" && ( "$workdir" == "$GITHUB_WORKSPACE" || "$workdir" == "$GITHUB_WORKSPACE/"* ) ]]; then
  echo 'FAIL: compatibility library must be built outside the source checkout' >&2
  exit 1
fi

# libxml2 2.14 changed SONAME to .16; the last 2.13 release retains .so.2.
# Official GNOME release archive and announced checksum, never an unpinned APT
# package or an unsafe symlink from libxml2.so.16 to libxml2.so.2.
version='2.13.9'
expected='a2c9ae7b770da34860050c309f903221c67830c86e4a7e760692b803df95143a'
url="https://download.gnome.org/sources/libxml2/2.13/libxml2-${version}.tar.xz"
mkdir -p "$workdir/source" "$workdir/build"
archive="$workdir/libxml2-${version}.tar.xz"
curl --fail --location --show-error --silent --retry 3 --retry-delay 2 --output "$archive" "$url"
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status || {
  echo 'FAIL: upstream libxml2 archive checksum mismatch' >&2
  exit 1
}
tar -xJf "$archive" -C "$workdir/source"
source_dir="$workdir/source/libxml2-${version}"
build_dir="$workdir/build"

# The library is a private BUILD-TIME dependency of LLVM, not an Aufake3D
# runtime artifact. Disable ICU and compression dependencies to avoid importing
# a second, unpinned old-library dependency tree from Ubuntu 24.04.
cmake -S "$source_dir" -B "$build_dir" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DBUILD_SHARED_LIBS=ON \
  -DLIBXML2_WITH_PYTHON=OFF \
  -DLIBXML2_WITH_PROGRAMS=OFF \
  -DLIBXML2_WITH_TESTS=OFF \
  -DLIBXML2_WITH_ICU=OFF \
  -DLIBXML2_WITH_LZMA=OFF \
  -DLIBXML2_WITH_ZLIB=OFF \
  -DLIBXML2_WITH_MODULES=OFF \
  -DLIBXML2_WITH_LEGACY=ON
cmake --build "$build_dir" --target LibXml2 --parallel 2

if [[ ! -f "$build_dir/libxml2.so.2" ]]; then
  echo 'FAIL: built libxml2 does not provide SONAME libxml2.so.2' >&2
  exit 1
fi
# Install the *verified build output* into LLVM's already-mounted private lib
# directory. In Ubuntu 26.10 containers runner.temp may be interpolated as a
# HOST path, whereas LLVM_PATH is guaranteed to be the mounted container path.
# A real .so.2 binary is copied, NOT a libxml2.so.16-to-.so.2 ABI symlink.
install -m 0644 "$build_dir/libxml2.so.2" "$LLVM_PATH/lib/libxml2.so.2"
export LD_LIBRARY_PATH="$LLVM_PATH/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

# Check the *actual* LLVM binary and every transitive dependency. Do not
# confuse a successful --version lookup with a successful dynamic-loader check.
ldd_output="$(ldd "$LLVM_PATH/bin/lld-link")"
printf '%s\n' "$ldd_output"
if grep -q 'not found' <<< "$ldd_output"; then
  echo 'FAIL: LLVM still has unresolved ELF shared-library dependencies' >&2
  exit 1
fi
if ! grep -Fq "libxml2.so.2 => $LLVM_PATH/lib/libxml2.so.2" <<< "$ldd_output"; then
  echo 'FAIL: LLVM is not loading the expected private, checked libxml2.so.2' >&2
  exit 1
fi
"$LLVM_PATH/bin/lld-link" --version
"$LLVM_PATH/bin/clang" --version | head -n 1

printf 'LD_LIBRARY_PATH=%s\n' "$LD_LIBRARY_PATH" >> "$GITHUB_ENV"
printf 'Private libxml2 SONAME=2 built from GNOME %s, archive SHA256=%s\n' "$version" "$expected"
