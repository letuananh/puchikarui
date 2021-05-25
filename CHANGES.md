# Changes

## puchikarui 0.2a2

- 2021-05-25
  - Switch off `auto_commit` when `buckmode` is enabled for much better performance
- 2021-05-24
  - Renamed old `ctx.select*()` functions `to query_*()`
    (The old `select()` was just `execute().fetchall()`)
  - Renamed `select_record()` to `select()`
  - Add `select_iter()` to allow avoiding fetchall()
  - Add `ctx.double()` function to use multiple cursors in a single ExecutionContext

## puchikarui 0.2a1

- [2021-05-19] Add MemorySource to fetch database into RAM before querying

## puchikarui 0.1 stable release

- [2021-05-13]

## puchikarui pre 0.1

- [2018-03-03] Auto expanduser path.
- [2018-01-24] First release to PyPI
- [2015-09-09] Reorganise project structure