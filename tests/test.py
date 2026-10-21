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


# A shared output directory must retain each requested LibCURL version.
def assert_libcurl_versions(versions):
    cache_dir = tempfile.mkdtemp("jbbversions")
    results = []
    for version in versions:
        libs = jbb.jbb(
            package=f"LibCURL-{version}",
            outdir=cache_dir,
            project="genotrance",
            quiet=False
        )
        assert libs and os.path.exists(libs[0]), f"LibCURL {version} was not extracted"
        assert version in libs[0], f"LibCURL {version} used the wrong extraction directory"
        results.append(libs[0])
    assert results[0] != results[1], "LibCURL versions shared an extraction directory"
    shutil.rmtree(cache_dir, ignore_errors=True)


assert_libcurl_versions(["v8.22.0", "v8.23.0"])
assert_libcurl_versions(["v8.23.0", "v8.22.0"])

# Metadata from JuliaBinaryWrappers and genotrance must use separate cache files.
project_dir = tempfile.mkdtemp("jbbprojects")
for project in [jbb.DEFAULT_PROJECT, "genotrance"]:
    libs = jbb.jbb(
        package="LibCURL-v8.22.0",
        outdir=project_dir,
        project=project,
        quiet=False
    )
    assert libs and os.path.exists(libs[0]), f"LibCURL was not extracted from {project}"
project_tomls = [name for name in os.listdir(project_dir) if name.startswith("Project-")]
assert len(project_tomls) >= 2, "projects reused one Project.toml cache file"
assert any(jbb.cache_name(jbb.DEFAULT_PROJECT) in name for name in project_tomls)
assert any(jbb.cache_name("genotrance") in name for name in project_tomls)
shutil.rmtree(project_dir, ignore_errors=True)

# Tags must be ordered by version number, not as strings
tag_dir = tempfile.mkdtemp("jbbtags")
jbb.DIR = tag_dir
with open(jbb.tag_path(jbb.DEFAULT_PROJECT, "Foo"), "w") as tf:
    for tag in ["Foo-v8.9.1+1", "Foo-v8.23.0+1", "Foo-v8.22.0+1", "Foo-v8.23.0+0",
                "Foo-v1.2.9+1", "Foo-v1.2.10+9", "Foo-v1.2.10+10", "Foo-v1.20.0+0"]:
        tf.write(f"0000 refs/tags/{tag}\n0000 refs/tags/{tag}^{{}}\n")
args = jbb.Args()
original_urlretrieve = jbb.urllib.request.urlretrieve
def offline_urlretrieve(*_args, **_kwargs):
    raise jbb.urllib.error.URLError("offline")
jbb.urllib.request.urlretrieve = offline_urlretrieve
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
jbb.urllib.request.urlretrieve = original_urlretrieve
shutil.rmtree(tag_dir, ignore_errors=True)

# Latest LibCURL from a custom project resolves to its highest version
tag_dir = tempfile.mkdtemp("jbbtags")
jbb.DIR = tag_dir
args = jbb.Args()
args.project = "genotrance"
latest = jbb.get_tag(args, "LibCURL", "")
with open(jbb.tag_path("genotrance", "LibCURL"), "r") as tf:
    tags = [line.split("refs/tags/")[-1].strip() for line in tf
            if "refs/tags/" in line and not line.strip().endswith("^{}")]
assert latest == max(tags, key=jbb.tag_version), f"LibCURL resolved to {latest}"
assert latest != "LibCURL-v8.9.1+1", "LibCURL resolved to the lexically largest tag"
shutil.rmtree(tag_dir, ignore_errors=True)
