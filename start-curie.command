#!/bin/sh
# Double-click this file to start Curie on a Mac (on Linux, run: sh start-curie.command).
# Options 1-3 install and download nothing. Option 4 asks before it downloads anything.
cd "$(dirname "$0")" || exit 1

open_page() {
    if command -v open >/dev/null 2>&1; then open "viewer/bench.html"
    elif command -v xdg-open >/dev/null 2>&1; then xdg-open "viewer/bench.html" >/dev/null 2>&1
    else echo "Open this file in your browser: $(pwd)/viewer/bench.html"; fi
}

find_python() {
    for p in python3 python; do
        if command -v "$p" >/dev/null 2>&1 && "$p" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
            PY=$p; return 0
        fi
    done
    echo
    echo "  Curie needs Python 3.10 or newer, and this computer does not have it."
    echo "  It is free: https://www.python.org/downloads/  Then double-click this file again."
    echo "  (Option 1, the wave bench, works without Python.)"
    return 1
}

xcheck() {
    echo
    echo "  This checks Curie against two independent simulators, Qiskit and Cirq."
    echo "  It downloads them (a few hundred MB) into a private folder here, .venv-xcheck,"
    echo "  so nothing else on this computer changes. Then it runs every test, including"
    echo "  300 random circuits compared against each simulator."
    printf "Go ahead? Type y and press Enter: "
    read -r ok || return 0
    case "$ok" in y|Y) ;; *) return 0 ;; esac
    [ -x .venv-xcheck/bin/python ] || "$PY" -m venv .venv-xcheck || return 1
    if ! .venv-xcheck/bin/python -m pip install --quiet -e ".[xcheck]" pytest; then
        echo "  The download or install did not finish. Check the internet connection and try again."
        return 1
    fi
    .venv-xcheck/bin/python -m pytest tests -q
    echo
    echo "  To remove the cross-checks later, delete the .venv-xcheck folder."
}

while :; do
    echo
    echo "  CURIE  -  a quantum-computation microscope"
    echo
    echo "  1. Open the wave bench in your browser   (no Python needed)"
    echo "  2. Run the lessons, step by step         (needs Python)"
    echo "  3. Run a guided tour                     (needs Python)"
    echo "  4. Check Curie against Qiskit and Cirq   (downloads them; asks first)"
    echo "  5. Quit"
    echo
    printf "Type a number and press Enter: "
    read -r pick || exit 0
    case "$pick" in
        1) open_page; echo "The wave bench is opening in your browser." ;;
        2) find_python && "$PY" -m curie lessons ;;
        3) find_python && "$PY" -m curie demo q1 ;;
        4) find_python && xcheck ;;
        5|"") exit 0 ;;
        *) echo "That was not 1, 2, 3, 4 or 5." ;;
    esac
done
