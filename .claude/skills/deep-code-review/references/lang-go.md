# Go red flags

Read this when the target contains Go. Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

## Go

- Ignored errors: `_ =` on a call that returns `error`, or no `if err != nil`.
- String-built SQL vs `db.Query(q, args...)`; `fmt.Sprintf` into a query.
- `exec.Command("sh", "-c", built)` → command injection.
- Goroutine leaks: a goroutine with no cancellation/`context`; `defer` inside a
  loop accumulating until function return.
- `math/rand` for security (use `crypto/rand`); missing `rows.Close()`;
  data races (run with `-race`; a flag/state shared across goroutines needs
  `sync/atomic` or a channel, not a plain field read); `panic` used for normal
  control flow.
- **Loop-variable capture in a closure/goroutine (pre-Go-1.22 semantics).** `for _, x := range xs { go func(){ use(x) }() }` shares **one** `x` across all iterations before Go 1.22, so the goroutines mostly see the last value. Go 1.22 gives each iteration a fresh variable — but the change follows the **module's declared `go` version in `go.mod`**, not the installed toolchain, so a vendored/legacy `go 1.20` module keeps the bug even built by a 1.22+ compiler. Check the `go.mod` directive, not `go version`; or capture explicitly (`x := x` / a param), which is correct under every version.
- **Channel-close discipline.** Sending on or closing a **closed** channel, and closing a **nil** channel, are **run-time panics**, not no-ops — two fan-in producers each `defer close(ch)` panics the second close. One owner closes; use `sync.Once` or a done-channel when ownership is shared.
- **Concurrent map access is a fatal crash, not a stale read.** An unsynchronized map write concurrent with any other access **can** be runtime-detected and abort the process (`fatal error: concurrent map writes`) even without `-race` — but the check is **best-effort** (the Go FAQ says it *can* crash), so a clean run is **not** proof of no concurrent access; an access the detector misses can still silently corrupt (the torn-value case in `concurrency-shared-state.md`). Guard with a mutex or use `sync.Map`.
