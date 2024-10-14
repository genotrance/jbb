"Download prebuilt libraries from Binary Builder"

import argparse
import os
import platform
import shutil
import sys
import urllib.request

DEFAULT_PROJECT = "JuliaBinaryWrappers"
DIR = None
DONE = []


class Args:
    package = None
    abi = ""
    arch = ""
    libc = ""
    os = ""
    project = ""
    sanitize = ""
    outdir = None
    static = False
    clean = False
    quiet = True


def get_arch():
    arch = platform.machine()
    if arch == "AMD64":
        arch = "x86_64"

    return arch


def get_os():
    if sys.platform == "linux":
        return "linux"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    else:
        raise ValueError("Unknown OS")


def get_libc():
    if sys.platform == "linux":
        return platform.libc_ver()[0] or "musl"
    else:
        return ""


def get_key(args=None):
    if args is None:
        args = Args()
        args.arch = get_arch()
        args.os = get_os()
        args.libc = get_libc()

    key = ""
    if len(args.arch) != 0 and len(args.os) != 0:
        key = f"{args.arch}-{args.os}"
    if len(args.libc) != 0:
        key += f"-{args.libc}"
    if len(args.abi) != 0:
        key += f"-{args.abi}"
    if len(args.sanitize) != 0:
        key += f"-{args.sanitize}"
    return key


OPTIONS = {
    "abi": {
        "short": "b",
        "choices": None,
        "default": "",
        "help": "ABI type if Linux"
    },
    "arch": {
        "short": "a",
        "choices": ["aarch64", "armv6l", "armv7l", "i686", "powerpc64le", "x86_64"],
        "default": get_arch(),
        "help": "target machine"
    },
    "outdir": {
        "short": "d",
        "choices": None,
        "default": "",
        "help": "output directory"
    },
    "libc": {
        "choices": ["glibc", "musl"],
        "default": "",
        "help": "libc type if Linux"
    },
    "os": {
        "choices": ["linux", "windows", "macos"],
        "default": get_os(),
        "help": "operating system"
    },
    "project": {
        "short": "p",
        "choices": None,
        "default": DEFAULT_PROJECT,
        "help": "GitHub project (user/repo)",
    },
    "sanitize": {
        "short": "z",
        "choices": ["memory"],
        "default": "",
        "help": "sanitizer type"
    }
}


def skip_until(lines, string):
    for line in lines:
        if string in line:
            break


def dl_file(args, package, url, path):
    if not os.path.exists(path):
        if not args.quiet:
            print("- Downloading " + path.split("/")[-1])
        try:
            urllib.request.urlretrieve(url % (args.project, package), path)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                if args.project != DEFAULT_PROJECT:
                    args.project = DEFAULT_PROJECT
                    return dl_file(args, package, url, path)
                else:
                    raise ValueError(f"Package {package} does not exist")
            else:
                raise e


def dl_tags(args, package):
    # Download all git tags for the package
    tagfile = f"{DIR}{os.path.sep}Tags_{package}.bin"
    url = "https://github.com/%s/%s_jll.jl.git/info/refs?service=git-upload-pack"
    dl_file(args, package, url, tagfile)
    return tagfile


def dl_toml(args, package, tag, file):
    # Download file.toml
    toml = f"{DIR}{os.path.sep}{file}-{package}.toml"
    url = "https://raw.githubusercontent.com/%s/%s_jll.jl/" + \
        f"{tag}/{file}.toml"
    dl_file(args, package, url, toml)
    return toml


def get_tag(args, package, version):
    # Get full version tag from package name if specified
    if len(version) != 0:
        ptag = f"{package}-{version}"
        tagfile = dl_tags(args, package)
        tags = []
        with open(tagfile, "r") as tf:
            for line in tf.readlines():
                if "refs/tags/" in line:
                    tag = line.split("refs/tags/")[-1].strip()
                    if not tag.endswith("^{}"):  # Exclude peeled tags
                        tags.append(tag)
        tags.sort(reverse=True)
        for tag in tags:
            if tag.startswith(ptag):
                return tag
        raise ValueError(f"{ptag} not found")
    return "main"


def get_deps(args, package, tag):
    # Download Package.toml
    toml = dl_toml(args, package, tag, "Project")

    # Load Package.toml
    reqs = []
    lines = iter(open(toml, "r").readlines())

    # Skip until [deps] section
    skip_until(lines, "[deps]")

    # Read all lines until empty line
    line = next(lines)
    while line != "\n":
        # Extract package name
        pkg = line.split(" ")[0]
        if pkg.endswith("_jll"):
            reqs.append(pkg[:-4])
        # Read next line
        line = next(lines)

    # Add version tags if compat defined
    lines = iter(open(toml, "r").readlines())

    # Skip until [compat] section
    skip_until(lines, "[compat]")

    # Read all lines until empty line
    line = next(lines)
    while True:
        # Extract package name
        pkg, version = line.strip().split(" = ", 1)
        if pkg.endswith("_jll"):
            pkgname = pkg[:-4]
            version = version.strip('"')
            if pkgname in reqs:
                idx = reqs.index(pkgname)
                reqs[idx] = f"{pkgname}-v{version}"
        try:
            # Read next line
            line = next(lines)
        except StopIteration:
            break

    return reqs


def get_urls(args, package, tag):
    # Download Artifacts.toml
    toml = dl_toml(args, package, tag, "Artifacts")

    # Load Artifacts.toml
    lines = iter(open(toml, "r").readlines())

    urls = {}
    myargs = Args()
    for line in lines:
        line = line.strip()
        if len(line) != 0:
            spl = line.split(" = ", 1)
            name = spl[0]
            val = spl[1].strip('"') if len(spl) == 2 else ""

            if name == "arch":
                myargs.arch = val
            elif name == "os":
                myargs.os = val
            elif name == "libc":
                myargs.libc = val
            elif name == "call_abi":
                myargs.abi = val
            elif name == "sanitize":
                myargs.sanitize = val
            elif name == "url":
                key = get_key(myargs)
                urls[key] = val
                myargs = Args()

    return urls


def get_jbb(args, package):
    # Remove version tag if present
    if package.count("-") > 0:
        package, version = package.split("-", 1)
    else:
        version = ""

    if package in DONE:
        return []

    if not args.quiet:
        print("Getting " + package)

    tag = get_tag(args, package, version)
    deps = get_deps(args, package, tag)
    urls = get_urls(args, package, tag)

    key = get_key(args)
    if key not in urls:
        if len(urls) == 1 and "" in urls:
            key = ""
        else:
            err = f"{key} not available. Available options:\n"
            for key in sorted(urls.keys()):
                err += f"  {key}\n"
            raise ValueError(err)

    # Download package
    url = urls[key]
    filename = f"{DIR}{os.path.sep}{url.split('/')[-1]}"
    fname = os.path.basename(filename)
    if not os.path.exists(filename):
        if not args.quiet:
            print("- Downloading " + fname)
        urllib.request.urlretrieve(url, filename)

    # Extract tgz with Python
    extracted = f"{DIR}{os.path.sep}{package}"
    if not os.path.exists(extracted):
        if not args.quiet:
            print("- Extracting " + fname)
        shutil.unpack_archive(filename, extracted)

    # Get path for libraries directory
    # Determine the correct library directory
    libdir = ""
    if sys.platform in ["linux", "darwin"]:
        if os.path.exists(f"{extracted}{os.path.sep}lib64"):
            libdir = "lib64"
        elif os.path.exists(f"{extracted}{os.path.sep}lib"):
            libdir = "lib"
    elif sys.platform == "win32":
        if os.path.exists(f"{extracted}{os.path.sep}bin"):
            libdir = "bin"

    # Add only if libdir exists
    libs = []
    if len(libdir):
        libs = [f"{extracted}{os.path.sep}{libdir}"]

    # Add to DONE
    DONE.append(package)

    for dep in deps:
        dep_libs = get_jbb(args, dep)
        if len(dep_libs) != 0:
            libs.extend(dep_libs)

    return libs


def setup(args):
    global DIR

    # Create output for jbb
    if len(args.outdir) == 0:
        DIR = f"lib{os.path.sep}{get_key(args)}"
    else:
        DIR = args.outdir

    DIR = os.path.abspath(DIR)

    os.makedirs(f"{DIR}", exist_ok=True)


def clean(args):
    if not args.clean:
        return

    if not args.quiet:
        print("Removing " + DIR)
    shutil.rmtree(DIR, ignore_errors=True)


def check_args(args):
    # Adjust libc
    if args.os == "linux" and args.libc == "":
        args.libc = get_libc()
    elif args.os != "linux" and args.libc != "":
        raise ValueError("libc is only valid for Linux")


def parse_args():
    # Create the argument parser
    parser = argparse.ArgumentParser(
        description="Download prebuilt libraries from Binary Builder")

    # Add the arguments
    parser.add_argument("package", type=str, nargs="+",
                        help="package/GitHub tag to download")
    for option, params in OPTIONS.items():
        short = params["short"] if "short" in params else option[0]
        parser.add_argument(f"-{short}", f"--{option}", type=str, choices=params["choices"],
                            default=params["default"], help=params["help"])
    parser.add_argument(
        "-s", "--static", action="store_true", help="copy .a files")
    parser.add_argument("-c", "--clean", action="store_true",
                        help="remove downloaded files")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="suppress output")

    # Parse and check the arguments
    args = parser.parse_args()
    check_args(args)

    return args

# Main function that takes the first argument and runs get_jbb() on it


def app(args):
    setup(args)
    libs = []
    for package in args.package:
        libs.extend(get_jbb(args, package))

    clean(args)

    return libs


def jbb(package, arch=None, os=None, libc=None, abi=None, sanitize=None, outdir=None, project=None, static=False, clean=False, quiet=True):
    """
    Run jbb with the specified package and optional arguments.

    Args:
        package (str or list): package/GitHub tag to download
        arch (str, optional): target machine - default: this platform
        os (str, optional): operating system - default: this platform
        libc (str, optional): libc type if Linux - default: this platform
        abi (str, optional): ABI type if Linux - default: this platform
        sanitize (str, optional): sanitizer type - default: ""
        outdir (str, optional): output directory - default: pwd/lib/arch-os[-libc]
        project (str, optional): GitHub project (user/repo) - default: JuliaBinaryWrappers
        static (bool, optional): copy .a files - default: .so/.dylib/.dll files
        clean (bool, optional): remove downloaded files - default: false
        quiet (bool, optional): suppress output - default: true

    Returns:
        [str]: directories where the libraries were downloaded

    Raises:
        ValueError
    """
    args = Args()
    args.static = static
    args.clean = clean
    args.quiet = quiet
    if len(package) == 0:
        if not args.quiet:
            print("No package specified")
        return None

    if type(package) == list:
        args.package = package
    elif type(package) == str:
        args.package = [package]
    else:
        raise ValueError(
            "Invalid package type - should be string or list of strings")

    for option, params in OPTIONS.items():
        if locals()[option] is not None:
            if params["choices"] is None:
                setattr(args, option, locals()[option])
            elif locals()[option] in params["choices"]:
                setattr(args, option, locals()[option])
            else:
                errstr = f"Invalid value for {option}: {locals()[option]}"
                raise ValueError(errstr)
        else:
            setattr(args, option, params["default"])

    check_args(args)

    return app(args)


def main():
    args = parse_args()

    try:
        libs = app(args)
    except ValueError as e:
        print(e.args[0])
        sys.exit(1)

    if not args.quiet:
        print("Downloaded to " + DIR)
    print(os.path.pathsep.join(libs))


if __name__ == "__main__":
    main()
