#! /bin/sh

set -e

# Build wheel if not exists or -f
if [ ! -d "dist" ] || [ "$1" = "--force" ]; then
    rm -rf build jbb.egg-info dist

    python3 -m pip install build twine
    python3 -m build -w
    rm -rf build
    python3 -m twine check dist/*
fi

test() {
    if [ ! -z "$1" ]; then
        source $1/bin/activate
    fi

    python3 -m pip install dist/jbb-*.whl --force-reinstall

    cd tests
    python3 test.py
    cd ..

    if [ ! -z "$1" ]; then
        deactivate
    fi
}

if [ "$1" = "--post" ]; then
    python3 -m twine upload dist/*
else
    PYVENV="$HOME/pyvenv"
    if [ -d "$PYVENV" ]; then
        for pyvenv in `ls -d $PYVENV/*`
        do
            test $pyvenv
        done
    else
        test ""
    fi
fi
