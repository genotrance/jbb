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

# Tags must be ordered by version number, not as strings
tag_dir = tempfile.mkdtemp("jbbtags")
jbb.DIR = tag_dir
with open(os.path.join(tag_dir, "Tags_Foo.bin"), "w") as tf:
    for tag in ["Foo-v8.9.1+1", "Foo-v8.23.0+1", "Foo-v8.22.0+1", "Foo-v8.23.0+0",
                "Foo-v1.2.9+1", "Foo-v1.2.10+9", "Foo-v1.2.10+10", "Foo-v1.20.0+0"]:
        tf.write(f"0000 refs/tags/{tag}\n0000 refs/tags/{tag}^{{}}\n")
args = jbb.Args()
expected = {
    "": "Foo-v8.23.0+1",
    "v8": "Foo-v8.23.0+1",
    "v8.9": "Foo-v8.9.1+1",
    "v8.23.0": "Foo-v8.23.0+1",
    "v8.23.0+0": "Foo-v8.23.0+0",
    "v1.2": "Foo-v1.2.10+10",
    "v1.20": "Foo-v1.20.0+0",
}
for version, tag in expected.items():
    found = jbb.get_tag(args, "Foo", version)
    assert found == tag, f"Foo-{version} resolved to {found}, expected {tag}"
try:
    jbb.get_tag(args, "Foo", "v8.2")
    raise AssertionError("Foo-v8.2 should not match v8.22 or v8.23")
except ValueError:
    pass
shutil.rmtree(tag_dir, ignore_errors=True)

# Latest LibCURL from a custom project resolves to its highest version
tag_dir = tempfile.mkdtemp("jbbtags")
jbb.DIR = tag_dir
args = jbb.Args()
args.project = "genotrance"
latest = jbb.get_tag(args, "LibCURL", "")
with open(os.path.join(tag_dir, "Tags_LibCURL.bin"), "r") as tf:
    tags = [line.split("refs/tags/")[-1].strip() for line in tf
            if "refs/tags/" in line and not line.strip().endswith("^{}")]
assert latest == max(tags, key=jbb.tag_version), f"LibCURL resolved to {latest}"
assert latest != "LibCURL-v8.9.1+1", "LibCURL resolved to the lexically largest tag"
shutil.rmtree(tag_dir, ignore_errors=True)
