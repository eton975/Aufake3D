# v0.2.9: Measured MIT KEMAR binaural prototype

The 0.2.8 front/back/up prototype was not convincingly directional in an actual headphone listening test.
This build replaces the analytical approximation with measured HRIR convolution from the **MIT KEMAR normal-pinna dataset** shipped by Debian libmysofa. Native input/output sample rates: 22,050, 44,100, and 48,000 Hz. Others use the v0.2.8 analytical fallback.

Provenance: `/usr/share/libmysofa/MIT_KEMAR_normal_pinna.sofa`, measured original 44.1 kHz, 710 directions, two ears. Resampled into 22.05 and 48 kHz arrays offline with `scipy.signal.resample_poly`. 320-tap truncation at 44.1 kHz retains most measured impulse-response energy but is not a perfect reconstruction. The 22.05 and 48 kHz outputs have 160 and 348 taps respectively. Directions are selected by nearest measured source vector. Generated C arrays are included inside the 32-bit DLL; no runtime SOFA loader or external files needed.

Copyright 1994, **Bill Gardner and Keith Martin, MIT Media Laboratory**. MIT KEMAR data provided free without restrictions on use if the authors are cited in research or commercial applications. This attribution is included in `win32/measured_hrir_data.h` and in this document. Original dataset data are not Aureal-specific HRTF coefficients.

Listening probe uses four-tenths of a second of low-amplitude faded *broadband noise* per position, through the **original Miles A3D2 provider**. Headphones and disabled additional spatialization/virtual surround are recommended. The source sample is entirely synthetic, no game files are modified. The output volume remains conservative.

**Limitations:** Generic HRIRs vary from person to person. Front/back/up may remain ambiguous even with measured HRTFs. No headphone equalization, head tracking, interpolation (nearest-position selection causes angular discontinuities), continuous mixer, reverb, occlusion, ray tracing, streaming, event timing, or A3D 2.0 Wavetracing. This remains a laboratory demonstration, not playable Alice or a Windows 10/11 drop-in release.
