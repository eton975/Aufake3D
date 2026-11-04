#!/usr/bin/env bash
# Host-local only: compile real libxml2.so.2 from checksum-pinned GNOME source
# for LLVM 19.1.7 when Debian/Ubuntu no longer provides that legacy SONAME.
# No apt changes, no root privileges, no fake .so.16 -> .so.2 links.
set -euo pipefail
if [[ $# -ne 2 ]]; then
    echo 'Usage: local_prepare_llvm_compat.sh LLVM_ROOT EXTERNAL_CACHE_DIRECTORY' >&2
    exit 2
fi
llvm_root="$1"
workdir="$2"
case "$llvm_root:$workdir" in
  *..*) echo 'FAIL: absolute trusted cache paths required' >&2; exit 2 ;;
esac
[[ "$llvm_root" = /* && "$workdir" = /* ]] || { echo 'FAIL: require absolute paths' >&2; exit 2; }
[[ -f "$llvm_root/bin/lld-link" ]] || { echo 'FAIL: LLVM linker missing' >&2; exit 1; }
for exe in curl sha256sum tar cmake ninja c++; do
  command -v "$exe" >/dev/null 2>&1 || { echo "FAIL: missing $exe for private libxml2 build" >&2; exit 1; }
done
version='2.13.9'
expected='a2c9ae7b770da34860050c309f903221c67830c86e4a7e760692b803df95143a'
url="https://download.gnome.org/sources/libxml2/2.13/libxml2-${version}.tar.xz"
mkdir -p "$workdir/source" "$workdir/build" "$llvm_root/lib"
archive="$workdir/libxml2-${version}.tar.xz"
if [[ ! -f "$archive" ]] || ! printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status; then
  curl --fail --location --show-error --silent --retry 3 --retry-delay 2 --output "$archive" "$url"
fi
printf '%s  %s\n' "$expected" "$archive" | sha256sum --check --status || {
    echo 'FAIL: upstream libxml2 source SHA-256 mismatch' >&2
    exit 1
}
if [[ ! -f "$workdir/source/libxml2-${version}/CMakeLists.txt" ]]; then
    tar -xJf "$archive" -C "$workdir/source"
fi
cmake -S "$workdir/source/libxml2-${version}" -B "$workdir/build" -G Ninja \
 -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON \
 -DLIBXML2_WITH_PYTHON=OFF -DLIBXML2_WITH_PROGRAMS=OFF -DLIBXML2_WITH_TESTS=OFF \
 -DLIBXML2_WITH_ICU=OFF -DLIBXML2_WITH_LZMA=OFF -DLIBXML2_WITH_ZLIB=OFF \
 -DLIBXML2_WITH_MODULES=OFF -DLIBXML2_WITH_LEGACY=ON
cmake --build "$workdir/build" --target LibXml2 --parallel 2
[[ -f "$workdir/build/libxml2.so.2" ]] || { echo 'FAIL: no real libxml2.so.2 was built' >&2; exit 1; }
install -m 0644 "$workdir/build/libxml2.so.2" "$llvm_root/lib/libxml2.so.2"
export LD_LIBRARY_PATH="$llvm_root/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd "$llvm_root/bin/lld-link" | tee "$workdir/llvm-lld-dependencies.txt"
if grep -q 'not found' "$workdir/llvm-lld-dependencies.txt"; then
  echo 'FAIL: LLVM still has unresolved host shared-library dependencies' >&2
  exit 1
fi
"$llvm_root/bin/lld-link" --version
