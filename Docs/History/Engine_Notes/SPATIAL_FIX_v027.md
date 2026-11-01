# v0.2.7 stereo-side correction and scope

User reported v0.2.6 was louder but left/right was **reversed** in the Miles-driven three-tone test.

The placeholder renderer used `up × forward` unconditionally as listener-right. That sign is wrong for A3D's **default right-handed** coordinate convention when the listener faces forward toward negative Z. The correct basis is `forward × up` for right-handed; `up × forward` for an explicitly selected left-handed system.

Corrections:
- Shared `win32/spatial_stereo.h` helper used by the actual DLL and compiled/native regression tests.
- Default A3D listener orientation RH: facing `(0,0,-1)`, up `(0,1,0)`.
- Respect `IA3d4::SetCoordinateSystem` 0 (right-handed) and 1 (left-handed).
- Output PCM interleaving remains **left 16-bit sample first, right second**.
- Diagnostic logs for listener forward/up, coordinate mode, pan and channel gain.
- Preserve v0.2.6 volume policy rather than make yet another gain adjustment.

Caveats: these tests establish the correctness of basic stereo directional math, not A3D HRTF authenticity. They cannot determine a user's physical headphone cable/OS routing. Do not install in the game directory; run in the isolated Wine research prefix. Native Windows drop-in DLL installation is not yet supported.

If the user still hears reversed channels in the v0.2.7 test, inspect the three per-process shim logs for `A3D.Renderer.pan_leftGain_rightGain` and `IA3dListener.OrientationForward` before making further changes; distinguish incoming world coordinates from left/right audio output routing.
