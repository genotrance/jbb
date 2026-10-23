## Download prebuilt libraries from [Binary Builder](https://binarybuilder.org/)

### Command line

```
usage: jbb.py [-h] [-b ABI] [-a {aarch64,armv6l,armv7l,i686,powerpc64le,x86_64}] [-d OUTDIR] [-l {glibc,musl}] [-o {linux,windows,macos}] [-p PROJECT] [-z {memory}] [-s] [-c] [-q] package [package ...]

Download prebuilt libraries from Binary Builder

positional arguments:
  package               package/GitHub tag to download

options:
  -h, --help            show this help message and exit
  -b --abi ABI          ABI type if Linux
  -a --arch {aarch64,armv6l,armv7l,i686,powerpc64le,x86_64}
                        target machine
  -d --outdir OUTDIR
                        output directory
  -l --libc {glibc,musl}
                        libc type if Linux
  -o --os {linux,windows,macos}
                        operating system
  -p --project PROJECT  GitHub project (user/repo)
  -z --sanitize {memory}
                        sanitizer type
  -s, --static          copy .a files
  -c, --clean           start with clean output directory
  -q, --quiet           suppress output
```

#### For example:
```
# python3 jbb.py libcurl -d /tmp/libcurl 
Getting libcurl
- Downloading Project-libcurl.toml
- Downloading Artifacts-libcurl.toml
- Downloading LibCURL.v8.9.1.x86_64-linux-gnu.tar.gz
- Extracting LibCURL.v8.9.1.x86_64-linux-gnu.tar.gz
Getting LibSSH2
- Downloading Project-LibSSH2.toml
- Downloading Artifacts-LibSSH2.toml
- Downloading LibSSH2.v1.11.2.x86_64-linux-gnu.tar.gz
- Extracting LibSSH2.v1.11.2.x86_64-linux-gnu.tar.gz
Getting OpenSSL
- Downloading Tags_OpenSSL.bin
- Downloading Project-OpenSSL.toml
- Downloading Artifacts-OpenSSL.toml
- Downloading OpenSSL.v3.0.15.x86_64-linux-gnu.tar.gz
- Extracting OpenSSL.v3.0.15.x86_64-linux-gnu.tar.gz
Getting nghttp2
- Downloading Project-nghttp2.toml
- Downloading Artifacts-nghttp2.toml
- Downloading nghttp2.v1.63.0.x86_64-linux-gnu.tar.gz
- Extracting nghttp2.v1.63.0.x86_64-linux-gnu.tar.gz
Getting Zlib
- Downloading Project-Zlib.toml
- Downloading Artifacts-Zlib.toml
- Downloading Zlib.v1.3.1.x86_64-linux-gnu.tar.gz
- Extracting Zlib.v1.3.1.x86_64-linux-gnu.tar.gz
Downloaded to /tmp/libcurl
/tmp/libcurl/libcurl/lib:/tmp/libcurl/LibSSH2/lib:/tmp/libcurl/OpenSSL/lib:/tmp/libcurl/nghttp2/lib:/tmp/libcurl/Zlib/lib

# export LD_LIBRARY_PATH=`python3 jbb.py libcurl -d /tmp/libcurl -q`
# echo $LD_LIBRARY_PATH
/tmp/libcurl/libcurl/lib:/tmp/libcurl/LibSSH2/lib:/tmp/libcurl/OpenSSL/lib:/tmp/libcurl/nghttp2/lib:/tmp/libcurl/Zlib/lib
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