# Aufake3D v0.8.13 — software licence scope (source-only edition)

The `LICENSE` file contains the standard proposed **MIT licence**, intended for independently authored Aufake3D code and documentation only to the extent the project contributors and publisher hold the necessary rights. **Publisher/copyright-holder sign-off is outstanding**: do not represent every file as conclusively cleared solely on the basis of this technical scan.

Exceptions and boundaries:

- `Source/Engine/acoustics/` retains its existing distinct MIT licence and copyright notice.
- MIT Media Laboratory KEMAR HRTF measurements embedded in `measured_hrir_data.h` are used under the measurement dataset's separate free-use-with-attribution terms; they are **not MIT-licensed by Aufake3D**.
- Historical Aureal SDK interface metadata informed the implementation. No original vendor SDK distributions are intentionally bundled. This is **not a strict clean-room** implementation.
- Original vendor Miles, game executables/data and VorpalFix are **not included** and not covered by Aufake3D's MIT grant.
- The **source** for the experimental Miles proxy and legacy helpers is retained for code review; their **prebuilt binaries are excluded** from this package. The proxy's exact binary can now be reconstructed from Aufake3D source and the published 331-name/ordinal export map without any original Miles DLL at build time. A legitimate original game-owned Miles DLL remains required at runtime; no vendor file is supplied. This technical reproducibility result does not settle any outstanding redistribution or rights questions.

See `THIRD_PARTY_NOTICES.md`, `LICENSE_STATUS.md`, and `SECURITY_RELEASE_REVIEW.md`.
