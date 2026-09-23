# C / C++ and Rust red flags

Read this when the target contains C, C++, or Rust (native or `unsafe` code; `method-situational.md` holds the matching memory-unsafe ground-truth rule). Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

## C / C++

- `strcpy`, `strcat`, `sprintf`, `gets`, `scanf("%s")` → buffer overflow; use
  bounded variants. Integer overflow before `malloc`; use-after-free / double
  free; `memcpy` with an unchecked length; format-string bugs (`printf(user)`).
- Run with ASan/UBSan (these map to top CWEs 787/416/125 — plus the classic/stack/heap
  buffer-overflow family, 120/121/122) — and **ThreadSanitizer**
  (`-fsanitize=thread`) for data races, which ASan/UBSan do **not** catch; state shared
  across threads needs `std::atomic` / an explicit `std::memory_order`, not a plain access.

## Rust

- **`unsafe` is a proof obligation, not an escape hatch — review each block for the invariant it asserts.** `std::mem::transmute` reinterprets bytes at a new type with **no validation**: transmuting to an enum value that isn't a declared discriminant, or to a `bool`/`char` outside its valid bit-patterns, is **immediate undefined behaviour**, not a wrong-but-defined value (the std docs flag transmute as a last resort). Prefer a checked conversion (`TryFrom`, `match`, `from_bits`).
- **`unsafe impl Send`/`Sync` silences the compiler's thread-safety check; it does not prove the property.** Wrapping a raw pointer / FFI handle to cross threads (`unsafe impl Send for Handle {}`) asserts a guarantee the compiler can no longer verify — if the pointee isn't actually safe to move/share (thread-affinity, interior aliasing), it is **silent UB with no backstop**, and "it compiles + tests pass" is not evidence (a normal run doesn't exercise UB). The Rustonomicon marks `Send`/`Sync` unsafe to implement for exactly this reason. Require a written safety argument per `unsafe impl` and confirm it holds.
- **Other `unsafe` tells:** a raw-pointer deref with unproven provenance/lifetime; `get_unchecked` / `unwrap_unchecked` without a checked invariant; `slice::from_raw_parts` with an unvalidated length; `MaybeUninit::assume_init` before full initialization. **Verify with `cargo miri`** (and ASan/TSan on the C/C++ side of any FFI boundary), or mark the block `unverified` (`method.md`) — the normal test suite does not exercise UB.
