# Aufake3D v0.8.14-RC1 — licensing and provenance audit

**Audit date:** 2026-11-02  
**Scope:** the actual v0.8.14-RC1 unified package, including all available source, game-kit binaries, utilities, generated HRTF data, tests and release metadata. This is a practical publication audit, **not a legal opinion or a clean-room certification**.

## Summary and decisions

| Class | Finding | Publication treatment |
|---|---|---|
| Aufake3D-authored C/C++/Python/shell code | Source present, largely marked as independently implemented; no separately licensed vendor source was identified by file-level inspection | **MIT proposed** for source controlled by its authors; final publisher/rights-holder sign-off required |
| Independent acoustics module | Separate MIT `LICENSE` already present | Retain original licence and copyright attribution |
| MIT KEMAR 1994 HRIR measurements | Data embedded as generated numerical tables; published no-restrictions-with-author-attribution permission verified | Include as **separately permitted data**, not relicense measurements under MIT; credit Gardner, Martin, MIT Media Lab |
| Aureal SDK API symbols, GUIDs, contracts | SDK used as reference for compatibility; not clean-room work | Document source/reference accurately; **never** redistribute original proprietary SDK files without authorisation |
| Original Miles vendor DLL/plugins | Not present in package | Must remain end-user-supplied and outside Git |
| Project's Miles naming proxy | Two bundled copies of project proxy; distinct hash from original Miles library; pinned 331-export table | Distribute with provenance warning; **exact proxy reproducibility and upstream rights review remain unresolved** |
| Aufake3D PE executables and core DLLs | Compiled artifacts included | Preserve binary hash inventory, acknowledge helper-specific reproducibility gaps |
| Retail games, VorpalFix, Aureal drivers | Not bundled | Do not redistribute |
| Trademarks | Names of Aureal, Miles, Unreal, Halo etc. are used for identification | No endorsement or trademark licence implied |

## Source audit method and limits

1. Enumerated the v0.8.14-RC1 ZIP file list, licence/notice files, executables, DLLs, static import libraries, generated assets and source headers.
2. Scanned text for copyright notices, third-party claims, licence markers, historic SDK/API references, hardcoded vendor paths and probable imported assets.
3. Compared long exact noncomment code lines (**80 characters or more**) between the project C/C++/header tree and 33 readable C/C++/header files in the supplied original Aureal SDK archive: **zero identical long code lines found** by that heuristic. This is only a weak screening test: shorter copied snippets, semantic rewrites and proprietary works are not ruled out.
4. Examined the HRTF table header and the original generator script; confirmed MIT KEMAR dataset attribution against the `libmysofa` source-package notice.
5. Compared installed universal core and proxy binary SHA-256 values against the frozen release, and checked build/installer source pathways. The universal core can be reproduced with the packaged tested recipe; exact proxy builds still need a compatible legally owned vendor export fixture.

**What this audit cannot establish:** legal authorship or contribution agreements; complete absence of copied third-party code; whether a proprietary export table used for the proxy is redistributable in every jurisdiction; patent or trademark clearance; or actual gameplay compatibility across all games and systems. A lawyer familiar with software reverse engineering can assess unresolved matters before a public MIT announcement.

## Most important actionable findings

1. **A project-wide top-level MIT licence was missing.** This package adds `LICENSE` and `LICENSE_SCOPE.md` for the independently authored code, while preserving older submodule notices. The rights holder must review and approve the copyright-holder line before posting to GitHub.
2. **HRTF measurements must not be called MIT software.** The original measurement grant requires authorship credit; the generated `measured_hrir_data.h` tables retain that status.
3. **The pinned Miles proxy is not entirely reproducible from a public clone.** `BUILDING.md` already documents the needed original Miles export fixture. No matching original vendor DLL is enclosed; the proxy is not a substitute for it.
4. **Prebuilt executable helpers need ongoing provenance checks.** A compiled core being reproducible does not automatically make every older diagnostic `.exe` reproducible. Mark old binaries as experimental until individually reverified.
5. **The project is not a strict clean-room reimplementation.** Historic SDKs were studied. Describe it as an independent interoperability implementation *informed by historical SDK references*.
6. **The present licence audit does not upgrade compatibility claims.** Alice 2011/Windows has an observed success with the unchanged v0.8.12 RC1 core; other games and Wine remain unverified in this release.

## Source publication checklist

- [ ] Copyright holder approves the MIT licence text and the `Aufake3D contributors` attribution (or supplies a preferred legal holder name).
- [ ] Contributors with independently owned material confirm licence compatibility/permission.
- [ ] Optional specialist legal review of SDK-based interface transcription and vendor export-table reconstruction.
- [x] Original vendor DLLs, retail game executables and VorpalFix are absent from the archive.
- [x] Separate KEMAR measurement attribution and acoustics-module MIT notice are present.
- [x] Original gameplay audio and retail copyrighted assets are absent from the normal runtime/game kits.
- [x] SHA-256 inventory and reusable verification script included.
- [ ] Final publisher selects whether to publish experimental legacy executables or release only the independently reproducible core and source on the initial GitHub tag.

See the accompanying `Docs/BINARY_PROVENANCE.md`, `Docs/PUBLICATION_CHECKLIST.md`, `LICENSE_SCOPE.md`, `THIRD_PARTY_NOTICES.md`, and `BUILDING.md`.

## Subsequent GitHub checkout audit (2026-11-02)

The original ZIP passed its self-check but **failed after `git clone`**: Git changed several text-file bytes via line-ending normalization, `.gitignore` excluded five release assets (two synthetic BSP fixtures and three small import libraries), and `verify_release.py` treated `.git` internals as unmanifested files. This preflight edition corrects those technical issues, preserves frozen runtime binary hashes, and tests an actual clean Git checkout. These changes are **technical readiness only**, not a legal clearance of code ownership or the prebuilt Miles compatibility proxy.
