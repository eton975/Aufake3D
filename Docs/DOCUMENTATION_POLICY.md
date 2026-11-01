# Documentation and review policy for contributors

A comment is useful when it explains a contract, non-obvious decision,
threading restriction or limitation—**not** when it repeats what a function name
already says. Keep comments adjacent to the invariant they protect.

Review checklist for a code change:

1. Identify affected ABI/API surfaces, PCM lifetimes, WaveOut ownership, or
   game-specific adapter assumptions; update the corresponding developer guide.
2. For source functions with nontrivial arguments, describe inputs, outputs,
   errors, ownership and concurrency where applicable.
3. Keep experimental branches labelled experimental. Do not silently convert
   an observed workaround into a proven root-cause claim.
4. Add regression coverage for the changed behaviour, compare core DLL hashes
   for no-op changes, and run the acoustics tests if geometry/HRTF code changes.
5. Preserve data attribution and export-table provenance. Never import original
   proprietary SDK implementation into a file that is presented as MIT-owned.
6. Update current docs; archive historical writeups instead of rewriting their
   recorded experiment results or merging old instructions into a live guide.

The generated `measured_hrir_data.h` is a numeric asset. Its data should not
be hand-commented or casually reformatted; identify provenance, generation
and licensing in surrounding documentation instead.
