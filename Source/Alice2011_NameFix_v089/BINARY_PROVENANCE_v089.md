# Proxy build provenance

Built from `miles_selection_v089.c` using the v0.8.6 export-compatible Miles stub (331 ordinals) for the **export table only**. That stub is NOT distributed and is not a replacement for the user's original Miles sound library. The proxy continues to resolve the genuine vendor Miles DLL from the user's installation at runtime as `a3d_mss_real.dll`; the suite verifies the vendor DLL hash before staging.

The new proxy changes ONLY the `a3d2_alias` string stored in the proxy's own writable memory when the real A3D2 handle opens successfully and the naming experiment is enabled. No game memory write/patch, no COM registration. The renderer and historical DLLs are unmodified.
