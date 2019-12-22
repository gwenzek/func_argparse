# set -x
SRC_FILES="func_argparse/ tests/ hello.py setup.py"
CONF=pyproject.toml

function _run_all() {
    res=0
    for cmd in "$@"; do
        echo "******** $cmd ********"
        $cmd
        res=$(($res + $?))
    done
    return $res
}

function _isort() {
    isort $1 -rc $SRC_FILES
    res=$?
    if [[ $1 == "--check" && $res != 0 ]]; then
        isort --diff -rc $SRC_FILES
    fi
    return $res
}

function _black() {
    black $1 $SRC_FILES
    res=$?
    if [[ $1 == --check && $res != 0 ]]; then
        black --diff $SRC_FILES
    fi
    return $res
}

function types() {
    # Runs Mypy
    mypy --config-file=$CONF $SRC_FILES
}

function fmt() {
    # Format code using isort and black. `fmt --check` to check formatting.
    _run_all "_isort $1" "_black $1"
}

function test() {
    # Run tests
    pytest -c $CONF
}

function all() {
    # Format, check types and tests.
    _run_all "fmt $1" types test
}

function release() {
    all --check
    rm -r dist
    python setup.py sdist bdist_wheel
    python -m twine upload -u gwenzek dist/*
}

$@
