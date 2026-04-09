#!/usr/bin/env python

import collections.abc
import contextlib
import dataclasses
import glob
import optparse
import os
import platform
import subprocess
import sys
import typing

REPO_ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

LIST_SYMBOLS = os.path.join(REPO_ROOT_DIR, "_build", "list_symbols")

@contextlib.contextmanager
def output(filename=None):
    if filename and filename != '-':
        filehandle = open(filename, 'w')
    else:
        filehandle = sys.stdout
    try:
        yield filehandle
    finally:
        if filehandle is not sys.stdout:
            filehandle.close()

@dataclasses.dataclass
class GhcInfo:
    header_files: list[str]
    library_file: str

    @staticmethod
    def from_ghc(ghc: str | None, include_path: str | None, library_file: str | None) -> typing.Optional['GhcInfo']:
        # if include_path and library_file are provided, use them as-is:
        if include_path and library_file:
            header_files = glob.glob(os.path.join(include_path, "**", "*.h"), recursive=True)
            return GhcInfo(header_files=header_files, library_file=library_file)
        # if ghc is not provided, find it on the path:
        if ghc is None:
            ghc = "ghc"
        # get the GHC version
        version_output = subprocess.run([ghc, '--numeric-version'], capture_output=True, encoding='utf-8')
        version = version_output.stdout.strip()
        # get the GHC libdir
        libdir_output = subprocess.run([ghc, '--print-libdir'], capture_output=True, encoding='utf-8')
        libdir = libdir_output.stdout.strip()
        # if include_path is provided...
        if include_path:
            # ...find all header files in the include_path...
            header_files = glob.glob(os.path.join(include_path, "**", "*.h"), recursive=True)
        else:
            # ...otherwise, find all header files in the libdir...
            header_files = glob.glob(os.path.join(libdir, f"*-ghc-{version}*", "rts-*", "include", "**", "*.h"), recursive=True)
        # if the librar_path is provided...
        if library_file:
            # ...use it as-is...
            pass
        else:
            # ...otherwise, search for the default rts library...
            if platform.system() == "Darwin":
                library_ext = "dylib"
            elif platform.system() == "Windows":
                library_ext = "dll"
            else:
                library_ext = "so"
            library_files = glob.glob(os.path.join(libdir, f"*-ghc-{version}*", f"libHSrts-ghc{version}.{library_ext}"))
            if len(library_files) != 1:
                return None
            library_file = library_files[0]
        return GhcInfo(header_files=header_files, library_file=library_files[0])

def list_symbols_in_headers(header_files: list[str]) -> set[str]:
    result = subprocess.run([LIST_SYMBOLS, *header_files], capture_output=True, encoding='utf-8')
    return set(
        line.strip()
        for line in result.stdout.split("\n")
    )

def list_symbols_in_library(library_file_file) -> set[str]:
    result = subprocess.run(["nm", "-gpU", library_file_file], capture_output=True, encoding='utf-8')
    return set(
        items[2].strip()
        for line in result.stdout.split("\n")
        for items in [line.split(' ')]
        if len(items) >= 3
    )

def main():
    parser = optparse.OptionParser()
    parser.add_option('-o', '--output')
    parser.add_option('-w', '--with-compiler')
    parser.add_option('-I', '--include-path')
    parser.add_option('-l', '--library-file')
    opts, args = parser.parse_args()

    # get header_files and library_file:
    ghc_info = GhcInfo.from_ghc(opts.with_compiler, opts.include_path, opts.library_file)

    # get the actual and expected symbols
    symbols_in_headers = list_symbols_in_headers(ghc_info.header_files)
    symbols_in_library = list_symbols_in_library(ghc_info.library_file)

    # get the unexpected symbols
    unexpected_symbols = list(sorted(symbols_in_library - symbols_in_headers))

    # output the unexpected symbols
    with output(opts.output) as o:
        o.writelines([f"{unexpected_symbol}\n" for unexpected_symbol in unexpected_symbols])

if __name__ == "__main__":
    main()
