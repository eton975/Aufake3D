# v0.4.5 — Post-spatial master loudness

Post-reverb global gain factor, default 1.5, overridable via `A3D_MASTER_GAIN`.
Stereo-linked sample peak limiter to 0.95 with ~0.00010 recovery/sample at 48 kHz,
state held across 256-frame blocks. No other rendering changes from v0.4.4.
Compiled/tested offline, not verified in actual Alice/Wine.
