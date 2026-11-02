# KLayout

The flow writes its GDS/OAS stream with the `klayout` Python module,
`pip install klayout`: a prebuilt wheel, with no Qt and nothing to
compile, for Linux (x86_64 and aarch64) and macOS. The installer
installs it with the other Python packages
(`etc/requirements-common_lock.txt`). `flow/util/def2stream.py`, run by
`PYTHON_EXE`, writes the file; without the module it stops with an
error and writes nothing:

```
ERROR: the klayout Python module is not installed, pip install klayout (etc/requirements-common_lock.txt)
```

DRC, LVS, the gallery and the viewers need the KLayout application,
which you install yourself: [KLayout](https://www.klayout.de/build.html).
The DRC and LVS rule decks are scripts in KLayout's Ruby-based DSL,
which the Python module does not include. None of them runs in the
default `make`.

## Makefile Targets

| Target | Requires KLayout | Description |
|---|---|---|
| `make finish` | The Python module | Complete flow including GDS generation |
| `make gds` | The Python module | Generate GDS/OAS from finished design |
| `make drc` | The application | Run DRC checks (requires GDS) |
| `make lvs` | The application | Run LVS checks (requires GDS) |
| `make gallery` | The application | Generate layout screenshots |
| `make klayout_<file>` | The application | Open result in KLayout viewer |
| `make generate_abstract` | No | Generate LEF/LIB abstracts |

A `check-klayout` guard produces a clear error message when the KLayout
application is missing and a target that needs it is invoked:

```
Error: KLayout not found. Install KLayout or set KLAYOUT_CMD.
Hint: KLayout is needed for DRC, LVS, the gallery and the viewers.
```

## bazel-orfs Integration

bazel-orfs uses the `do-` prefixed targets which bypass Make's dependency
management. `do-finish` / `do-final` only run the finish stage recipe
itself, while `make finish` also pulls in the GDS target as a Make
dependency. `do-gds` runs GDS generation separately.

An `orfs_gds()` Bazel rule can call `do-gds` independently from
`orfs_flow()`, making KLayout an optional toolchain dependency configured
in `MODULE.bazel`.

## KLayout Tech File Generation

The `do-klayout` and `do-klayout_wrap` targets generate `.lyt` technology
files by substituting LEF and map file paths into platform templates.
This is implemented in `util/generate_klayout_tech.py` using stdlib XML
processing — no KLayout dependency required.

## Testing Without KLayout

Unit tests for all KLayout-related Python scripts use `unittest.mock` to
mock the `pya` API:

```
cd flow/test
python -m unittest test_generate_klayout_tech test_def2stream test_convertDrc test_klayout_sh
```

These tests cover:
- `.lyt` tech file generation (`test_generate_klayout_tech.py`)
- DEF-to-GDS merging logic, and the error without the Python module (`test_def2stream.py`)
- DRC report conversion (`test_convertDrc.py`)
