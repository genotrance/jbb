import os
import shutil
import sys
import tempfile

import jbb

# Delete zlib directory if it exists
zlib_dir = tempfile.mkdtemp("jbbtest")
shutil.rmtree(zlib_dir, ignore_errors=True)

libs = jbb.jbb(
    package="Zlib-v1.2",
    outdir=zlib_dir,
    quiet=False
)

# Check if libz.so exists in the first library directory
if sys.platform == "win32":
    ext = "dll"
elif sys.platform == "darwin":
    ext = "dylib"
else:
    ext = "so"
assert os.path.exists(os.path.join(libs[0], f"libz.{ext}")), \
    f"libz.{ext} not found in {libs[0]}"

shutil.rmtree(zlib_dir, ignore_errors=True)
