## Download prebuilt libraries from [Binary Builder](https://binarybuilder.org/)

### Command line

```
usage: jbb.py [-h] [-b ABI] [-a {aarch64,armv6l,armv7l,i686,powerpc64le,x86_64}] [-d OUTDIR] [-l {glibc,musl}] [-o {linux,windows,macos}] [-s {memory}] [-t] [-c] [-q] package [package ...]

Download prebuilt libraries from Binary Builder

positional arguments:
  package               package to download

options:
  -h, --help            show this help message and exit
  -b --abi ABI     ABI type if Linux
  -a --arch {aarch64,armv6l,armv7l,i686,powerpc64le,x86_64}
                        target machine
  -d --outdir OUTDIR
                        output directory
  -l --libc {glibc,musl}
                        libc type if Linux
  -o --os {linux,windows,macos}
                        operating system
  -s --sanitize {memory}
                        sanitizer type
  -t --static          copy .a files instead of .so/.dylib/.dll files
  -c --clean           remove downloaded files
  -q --quiet           suppress output
```

#### For example:
```
# python3 jbb.py libcurl

Getting libcurl
- Downloading Project-libcurl.toml
- Downloading Artifacts-libcurl.toml
- Downloading LibCURL.v8.6.0.x86_64-linux-musl.tar.gz
- Extracting LibCURL.v8.6.0.x86_64-linux-musl.tar.gz
- Copying libraries
Getting libssh2
- Downloading Project-libssh2.toml
- Downloading Artifacts-libssh2.toml
- Downloading LibSSH2.v1.11.0.x86_64-linux-musl.tar.gz
- Extracting LibSSH2.v1.11.0.x86_64-linux-musl.tar.gz
- Copying libraries
Getting mbedtls
- Downloading Project-mbedtls.toml
- Downloading Artifacts-mbedtls.toml
- Downloading MbedTLS.v2.28.6.x86_64-linux-musl.tar.gz
- Extracting MbedTLS.v2.28.6.x86_64-linux-musl.tar.gz
- Copying libraries
Getting nghttp2
- Downloading Project-nghttp2.toml
- Downloading Artifacts-nghttp2.toml
- Downloading nghttp2.v1.59.0.x86_64-linux-musl.tar.gz
- Extracting nghttp2.v1.59.0.x86_64-linux-musl.tar.gz
- Copying libraries
Getting mbedtls
- Copying libraries
Getting zlib
- Downloading Project-zlib.toml
- Downloading Artifacts-zlib.toml
- Downloading Zlib.v1.3.1.x86_64-linux-musl.tar.gz
- Extracting Zlib.v1.3.1.x86_64-linux-musl.tar.gz
- Copying libraries
Downloaded to lib/x86_64-linux-musl

# ls -1 lib/x86_64-linux-musl
dl
libcurl.so.4
libmbedcrypto.so.7
libmbedtls.so.14
libmbedx509.so.1
libnghttp2.so.14
libssh2.so.1
libz.so.1

# export LD_LIBRARY_PATH=`pwd`/lib/linux-musl-x86_64
```

### API

```python
import os

import jbb

jbb.jbb(
    package = "zlib",
    outdir=os.path.join(os.getcwd(), "zlib"),
    arch="x86_64",
    os="linux",
    libc="musl",
    quiet=False
)
```