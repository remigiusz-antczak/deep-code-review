# Java / Kotlin red flags

Read this when the target contains Java or Kotlin. Split from `language-stack-redflags.md`; its fast first pass and cross-language sections apply to every review, and each hit here is a signal, not a verdict.

## Java / Kotlin

- `ObjectInputStream.readObject` on untrusted bytes → deserialization RCE.
- XXE: `DocumentBuilderFactory`/`SAXParser` without disabling external entities.
- `Runtime.exec`/`ProcessBuilder` with a concatenated string.
- String-built JPQL/SQL vs `PreparedStatement`/bound params.
- `Random` for tokens (use `SecureRandom`); swallowed `catch (Exception e) {}`;
  `printStackTrace()` to the response; broad `@SuppressWarnings`; a field shared across
  threads read without `volatile` / `synchronized` / an `AtomicX` (double-checked
  locking with a non-`volatile` instance field is broken).
- **A mutable field used in `equals()`/`hashCode()` corrupts hash-key lookups.** Mutating a field that participates in `hashCode()` **after** the object is put in a `HashMap`/`HashSet` leaves it physically in the *old* bucket; a later `get`/`contains` computes the *new* hash, looks in a different bucket, and returns **not-found** with no exception (iteration/`remove` corrupt likewise). A hash-key must be effectively immutable over its `hashCode` fields while in the collection; and every field used in `hashCode()` must also be in `equals()` — a `hashCode()` that includes a field `equals()` ignores breaks the contract directly (two equal objects then hash differently); excluding an `equals()`-only field from `hashCode()` merely costs bucket distribution (Bloch). Classic trigger: a JPA `@Entity` or Lombok `@EqualsAndHashCode` over a mutable id/status.
