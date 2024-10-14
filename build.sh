#! /bin/sh

# ./build.sh
#     --force - install deps and build wheel
#     --test  - test with tox on all versions of Python
#     --post  - post wheel to PyPI

set -e

if [ -z "$PY" ]; then
    echo "PY not set"
    PY=python3
fi

if [ -z "$TMP" ]; then
  TMP=/tmp
fi

if [ ! -d "dist" ] || [ "$1" = "--force" ]; then
    # Build wheels if missing or --wheel
    rm -rf build jbb.egg-info dist
    $PY -m pip install build twine
    $PY -m build -w
    rm -rf build
    $PY -m twine check dist/*
fi

if [ "$1" = "--post" ]; then
    # Upload wheel to PyPI
    $PY -m twine upload dist/*
elif [ "$1" = "--test" ]; then
    if [ -f "/.dockerenv" ] || [ "$OS" = "darwin" ] || [[ "$OS" = "windows"* ]]; then
        # Run tests with tox
        $PY -m pip install tox
        $PY -m tox --installpkg dist/jbb-*.whl --workdir $TMP
    else
        # Run tests in containers for linux
        for arch in x86_64 i686 aarch64; do
            for abi in musllinux_1_1_ manylinux2014_; do
                # Set PY to cp312
                docker run -it --rm -w /jbb -v `pwd`:/jbb -e PY=/opt/python/cp312-cp312/bin/python3 \
                    quay.io/pypa/$abi$arch /jbb/build.sh --test
            done
        done
    fi
fi
