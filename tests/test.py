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
