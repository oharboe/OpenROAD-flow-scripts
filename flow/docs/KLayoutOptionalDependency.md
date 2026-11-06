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

A DRC deck written in Python (`KLAYOUT_DRC_FILE` ends in `.py`) runs
on the Python module too: `flow/util/klayout_drc.py` loads the GDS,
runs the deck and writes the `.lyrdb` report. The decks are translated
line by line from KLayout's Ruby-based DRC language, which the Python
module does not include (KLayout/klayout#1772); that language is a thin
layer over `klayout.db`'s `Region`, `Edges` and `EdgePairs`
(KLayout/klayout#1980), and `klayout_drc.py` is that layer for the
operations the decks use. Python decks: asap7, nangate45, sky130hd,
ihp-sg13g2 (sg13g2_minimal).

An LVS deck written in Python (`KLAYOUT_LVS_FILE` ends in `.py`) runs
the same way: `flow/util/klayout_lvs.py` adds device extraction, the
CDL schematic and `NetlistComparer` to it, and writes the `.lvsdb`.
Python LVS decks: sky130hd.

A deck still written in the Ruby-based language, the gallery and the
viewers need the KLayout application, which you install yourself:
[KLayout](https://www.klayout.de/build.html). None of DRC or LVS runs
in the default `make`.

## Makefile Targets

| Target | Requires KLayout | Description |
|---|---|---|
| `make finish` | The Python module | Complete flow including GDS generation |
| `make gds` | The Python module | Generate GDS/OAS from finished design |
| `make drc` | The Python module for a `.py` deck, else the application | Run DRC checks (requires GDS) |
| `make lvs` | The Python module for a `.py` deck, else the application | Run LVS checks (requires GDS) |
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

`test_klayout_drc.py` runs the checks of `flow/util/klayout_drc.py` on a
small generated layout with the klayout Python module, and is skipped
without it.
