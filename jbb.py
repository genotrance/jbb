"Download prebuilt libraries from Binary Builder"

import argparse
import glob
import os
import platform
import shutil
import sys
import time
import urllib.request

BASEURL = "https://github.com/JuliaBinaryWrappers"
DIR = None

class Args:
    package = None
    abi= ""
    arch = ""
    libc = ""
    os = ""
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
    "sanitize": {
        "choices": ["memory"],
        "default": "",
        "help": "sanitizer type"
    }
}

def skip_until(lines, string):
    for line in lines:
        if string in line:
            break

def dl_toml(args, package, file):
    # Download file.toml
    toml = f"{DIR}/dl/{file}-{package[:-7]}.toml"
    if not os.path.exists(toml):
        if not args.quiet:
            print("- Downloading " + toml.split("/")[-1])
        try:
            urllib.request.urlretrieve(
                f"https://raw.githubusercontent.com/JuliaBinaryWrappers/{package}/main/{file}.toml",
                toml)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError(f"Package {package[:-7]} does not exist")
            else:
                raise e
    return toml

def get_deps(args, package):
    # Download Package.toml
    toml = dl_toml(args, package, "Project")

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
            reqs.append(pkg[:-4].lower())
        # Read next line
        line = next(lines)

    return reqs

def get_urls(args, package):
    # Download Artifacts.toml
    toml = dl_toml(args, package, "Artifacts")

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
    if not args.quiet:
        print("Getting " + package)

    # Add _jll.jl to package name
    package += "_jll.jl"

    deps = get_deps(args, package)
    urls = get_urls(args, package)

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
    filename = f"{DIR}/dl/{url.split('/')[-1]}"
    fname = os.path.basename(filename)
    if not os.path.exists(filename):
        if not args.quiet:
            print("- Downloading " + fname)
        urllib.request.urlretrieve(url, filename)

    # Extract tgz with Python
    extracted = f"{DIR}/dl/{package}"
    if not os.path.exists(extracted):
        if not args.quiet:
            print("- Extracting " + fname)
        shutil.unpack_archive(filename, extracted)

    # Move libraries into lib
    if not args.quiet:
        print("- Copying libraries")
    if not args.static:
        dots = 3
        if args.os == "linux":
            match = "lib/*.so.*"
        elif args.os == "macos":
            match = "lib/*.*.dylib"
        elif args.os == "windows":
            match = "bin/*.dll"
            dots = 2
    else:
        match = "lib/*.a"
        dots = 2
    for file in glob.glob(f"{extracted}/{match}"):
        fname = os.path.basename(file)
        if len(fname.split(".")) == dots and not os.path.exists(f"{DIR}/{fname}"):
            shutil.copy(file, f"{DIR}/.")

    for dep in deps:
        get_jbb(args, dep)

def setup(args):
    global DIR

    # Create output for jbb
    if len(args.outdir) == 0:
        DIR = f"lib/{get_key(args)}"
    else:
        DIR = args.outdir

    os.makedirs(f"{DIR}/dl", exist_ok=True)

def clean(args):
    if not args.clean:
        return

    dldir = f"{DIR}/dl"
    if not args.quiet:
        print("Removing " + dldir)
    shutil.rmtree(dldir, ignore_errors=True)

def check_args(args):
    # Adjust libc
    if args.os == "linux" and args.libc == "":
        args.libc = get_libc()
    elif args.os != "linux" and args.libc != "":
        raise ValueError("libc is only valid for Linux")

def parse_args():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Download prebuilt libraries from Binary Builder")

    # Add the arguments
    parser.add_argument("package", type=str, nargs="+", help="package to download")
    for option, params in OPTIONS.items():
        short = params["short"] if "short" in params else option[0]
        parser.add_argument(f"-{short}", f"--{option}", type=str, choices=params["choices"],
                            default=params["default"], help=params["help"])
    parser.add_argument("-t", "--static", action="store_true", help="copy .a files instead of .so/.dylib/.dll files")
    parser.add_argument("-c", "--clean", action="store_true", help="remove downloaded files")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress output")

    # Parse and check the arguments
    args = parser.parse_args()
    check_args(args)

    return args

# Main function that takes the first argument and runs get_jbb() on it
def app(args):
    setup(args)
    for package in args.package:
        get_jbb(args, package)

    clean(args)

    return DIR

def jbb(package, arch=None, os=None, libc=None, abi=None, sanitize=None, outdir=None, static=False, clean=False, quiet=True):
    """
    Run jbb with the specified package and optional arguments.

    Args:
        package (str or list): package(s) to be processed
        arch (str, optional): architecture - default: this platform
        os (str, optional): operating system - default: this platform
        libc (str, optional): libc type for Linux - default: this platform
        abi (str, optional): ABI type for Linux - default: this platform
        sanitize (str, optional): sanitizer type - default: ""
        outdir (str, optional): output directory - default: pwd/lib/arch-os[-libc]
        static (bool, optional): copy .a files - default: copy .so/.dylib/.dll files
        clean (bool, optional): remove downloaded files - default: false
        quiet (bool, optional): suppress output - default: true

    Returns:
        str: directory where the libraries were downloaded (outdir)

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
        raise ValueError("Invalid package type - should be string or list of strings")

    for option, params in OPTIONS.items():
        if locals()[option] is not None:
            if params["choices"] is None:
                setattr(args, option, locals()[option])
            elif locals()[option] in params["choices"]:
                setattr(args, option, locals()[option])
            else:
                raise ValueError(f"Invalid value for {option}: {locals()[option]}")
        else:
            setattr(args, option, params["default"])

    check_args(args)

    return app(args)

def main():
    args = parse_args()

    try:
        app(args)
    except ValueError as e:
        print(e.args[0])
        sys.exit(1)

    if not args.quiet:
        print("Downloaded to " + DIR)

if __name__ == "__main__":
    main()