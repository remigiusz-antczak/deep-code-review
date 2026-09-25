# Application security depth — cryptographic usage (A04)

Read this when the target or diff encrypts or decrypts (cipher mode, IV, nonce), compares a signature, token, API key, or OTP against caller input, hashes passwords (KDF cost parameters), wraps keys (DEK / KEK), holds data that must stay confidential for years, or suggests a keygen/secret-printing command to the user. Split from `security-appsec.md`, whose per-category core checks (access control, injection, secrets, input validation, SSRF) apply to every application review.

## A04:2025 — Cryptographic Failures (depth)

**Crypto-agility & post-quantum readiness.** Beyond using strong *current* primitives, check the code can **change**
them: algorithm choices named in config / metadata (a versioned suite id), not hard-coded at each call site, so a
primitive can be rotated without a rewrite — and a ciphertext / signature envelope carries an algorithm identifier so
old and new can coexist during a migration. For **long-lived** confidentiality (data or secrets that must stay secret
for years), weigh **harvest-now-decrypt-later**: an adversary can record classical-encrypted traffic today and decrypt
it once a cryptographically-relevant quantum computer exists — so long-lived secrets warrant a migration path to the
NIST post-quantum standards: **FIPS 203 ML-KEM** (key encapsulation), **FIPS 204 ML-DSA** and **FIPS 205 SLH-DSA**
(signatures), published 2024. Not every system needs PQC now; the finding is a
**hard-coded, un-versioned primitive with no swap path on a long-lived-data surface** — not "you must ship ML-KEM
today" (that would be stricter than the standard).

**Nonce/IV reuse is a forgery bug for AEAD ciphers, not merely a leak — "unique" and "unpredictable" are different bars.**
The "unique per message" rule in `security-appsec.md` A04 doesn't say what breaks, or how much, when it's violated. For **AES-GCM** (or any
AEAD built on GHASH), NIST's requirement is exact: "The probability that the authenticated encryption function ever
will be invoked with the same IV and the same key on two (or more) distinct sets of input data shall be no greater
than 2^-32" (NIST SP 800-38D §8). Break it and, per Appendix A, "it is likely that an adversary will be able to
determine the hash subkey from the resulting ciphertexts. The adversary then could easily construct a ciphertext
forgery... the authentication assurance essentially is lost. Worse, the loss of authentication means that GCM inherits
the problematic malleability of its Counter mode ciphertext... the adversary essentially could control the plaintext
output of the authenticated decryption function." That is CWE-323 ("Reusing a Nonce, Key Pair in Encryption") — pin
severity with the exposure-boundary discriminator (`security-appsec.md` A01) rather than a flat default — and it's current, not historical:
CVE-2024-36289 (a social-networking app reusing a nonce/key pair, letting an MITM manipulate direct messages) and
CVE-2024-21530 (a Rust package reusing one on object clone, resetting the RNG).

CBC/CFB's bar is stricter than "unique": NIST SP 800-38A requires the IVs "be unpredictable. In particular, for any
given plaintext, it must not be possible to predict the IV that will be associated to the plaintext in advance of the
generation of the IV" — a sequential, attacker-visible counter IV can be unique and still fail this. CTR/OFB reuse
instead compromises the confidentiality of the two messages wherever they overlap — the keystream repeats from the
first block, so every aligned block position leaks (a two-time-pad break), not merely an occasional block (SP 800-38A)
— on top of Counter-mode's existing bit-flip malleability.

Detect at the call site, not the algorithm name: is the nonce/IV drawn fresh from a CSPRNG (or SP 800-38A's own
Appendix B/C construction) immediately before **every** encryption call, or is it a module-level constant, a config
value, a counter with no durable high-water mark across restarts, or a value that survives an object clone?
**🚩 grep**: a hard-coded/all-zero IV constant; an IV assigned once outside the encrypt call; a counter reset on
process start; `clone`/`copy` on a struct carrying cipher state.

**A hand-rolled equality check on a secret-derived value is a timing side channel — generalize it across every raw-secret compare, not only the webhook and admit-gate instances already named.**
Comparing an HMAC/webhook signature, session/CSRF token, API key, or OTP/reset code against caller input with a
short-circuiting equality (`==`, `.equals()`, `strcmp`, `Arrays.equals`) leaks the position of the first mismatched
byte through response timing — CWE-208, "Observable Timing Discrepancy": "Two separate operations in a product require
different amounts of time to complete, in a way that is observable to an actor and reveals security-relevant
information about the state of the product, such as whether a particular operation was successful or not." Not
theoretical: CVE-2019-10071 is a Java framework comparing HMAC signatures with `String.equals()` instead of a
constant-time algorithm. The webhook-signature check (`api-contracts.md` § Webhooks — consuming) and the
admit-gate-entropy aside in `security-appsec.md` A07 both name this same primitive — a shared secret, API key, webhook-signing key,
or admin token compared against caller input — so this generalizes it to any raw secret-byte compare, anywhere.
(Distinct from account-enumeration in `security-appsec.md` A07, which equalizes response time across a *whole* signup/login/reset
request path to hide existence — a coarser, whole-endpoint timing control, not a byte-by-byte secret compare.
bcrypt/argon2 `verify()` calls are already constant-time internally — the gap here is a hand-rolled compare elsewhere:
session tokens, CSRF tokens, OTP/2FA, reset codes, API keys.)

Two vendor gotchas belong in the fix. Node's `crypto.timingSafeEqual` requires equal-length inputs — "a and b must
both be Buffers, TypedArrays, or DataViews, and they must have the same byte length. An error is thrown if a and b
have different byte lengths" — so calling it on a raw, variable-length, attacker-controlled candidate either throws,
or, if pre-checked with `a.length === b.length` to dodge the throw, reintroduces a smaller length-timing leak; compare
fixed-length values instead (HMAC-then-compare, or hash both sides first). Java's safe primitive is the **static**
`MessageDigest.isEqual(byte[], byte[])`, not `.equals()`/`Arrays.equals()` (CVE-2019-10071's exact mistake) — per the
Javadoc's Implementation Note: "The calculation time depends only on the length of digesta. It does not depend on the
length of digestb or the contents of digesta and digestb."

**🚩 grep**: `==`/`.equals()`/`Arrays.equals`/`strcmp` comparing a
`signature`/`hmac`/`token`/`csrf`/`otp`/`code`/`apiKey`-named variable against a request-derived value, with no
`timingSafeEqual`/`hmac.compare_digest`/`MessageDigest.isEqual`/ `subtle.ConstantTimeCompare` (Go) in the same
function.

**The algorithm name is not the control — the cost parameters are, and the floor is a moving target.** The `security-appsec.md` A04 check
("hashed with a memory-hard KDF... never fast hashes") verifies *which function* runs, not *how expensively*:
`argon2.hash(pw, { memoryCost: 512, timeCost: 1 })` and `bcrypt.hash(pw, 4)` both call a compliant KDF and pass a
name-only check while sitting far below any current floor — commonly a cost turned down "for fast tests" that ships to
prod unnoticed. Read the call-site arguments (memory/time/parallelism for Argon2id; work factor for bcrypt; N/r/p for
scrypt) against the **current** OWASP Password Storage Cheat Sheet floor — quoted for today's date only, not as
permanent doctrine: "Use Argon2id with a minimum configuration of 19 MiB of memory, an iteration count of 2, and 1
degree of parallelism. If Argon2id is not available, use scrypt with a minimum CPU/memory cost parameter of (2^17)...
For legacy systems using bcrypt, use a work factor of 10 or more and with a password limit of 72 bytes" — bcrypt
specifically only "for password storage in legacy systems where Argon2 and scrypt are not available." The floor rises
as hardware gets cheaper — re-check the cheat sheet at review time; don't hard-pin today's numbers as a permanent
gate.

**🚩 grep**: a KDF call whose numeric argument sits below the current floor cited above (today, that means: a
single-digit bcrypt work factor, an Argon2 `memoryCost`/`timeCost` far under the cited figures, a `scrypt` cost under
`2^17`) — or no visible parameter at all, meaning the library default is in effect and must be checked against the
same floor.

**Envelope encryption needs two independent keys, not one key filling both roles.** An application doing its own
field/record-level key wrapping — a Data Encryption Key (DEK) that encrypts the data, wrapped by a Key Encryption Key
(KEK) — must keep the two separate. OWASP's Cryptographic Storage Cheat Sheet, § Encrypting Stored Keys: "At least two
separate keys are required for this: The Data Encryption Key (DEK) is used to encrypt the data. The Key Encryption Key
(KEK) is used to encrypt the DEK. For this to be effective, the KEK must be stored separately from the DEK," and "The
KEK should also be at least as strong as the DEK." Reusing one key as both collapses the boundary the two-key design
exists to provide — a KEK compromise then directly exposes every DEK it wrapped, not only the data behind the one key
an attacker actually reached. Scope: hand-rolled/manual key wrapping only — pure-KMS delegation enforces this
internally and is out of scope.

**A suggested command that prints a generated secret to the current session leaks it into
the transcript.** Guidance (human- or agent-authored) that tells the operator to generate a
credential — an API key, a signing secret, a keypair — by running a command **in the same
interactive session** that is being logged/transcribed puts the plaintext secret into that
log the moment the command's stdout is echoed, even when the secret is never committed to a
file (one observed case: a suggested in-session keygen command printed the secret straight
into the transcript). Never suggest a command whose normal output is the secret itself when
that output lands in a shared/logged surface. Generate it in a **separate, untranscribed**
terminal, or have the command write directly to a **gitignored** file (`>` to the file, not
to stdout) so the value never appears as command output at all. **Check:** no suggested
command in-session prints keygen/secret-generation output to stdout.
