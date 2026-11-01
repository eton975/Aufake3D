# Next validation gate

The next *necessary* external validation is one isolated, user-controlled Wine run of the new v0.3.1 streaming DLL and Alice itself, after completing the remaining offline static/ABI assessment. No data from the physical Vortex 2, PCI bus, BIOS or kernel driver is needed.

Before requesting a user run, address:

- real audio thread shutdown and COM object/source lifetime under concurrent API updates;
- event registrations and Miles' expected PCM-buffer queue semantics;
- precise Alice provider selection vs the previously observed Miles Fast 2D fallback;
- actual submission of acoustic geometry / material properties from Alice;
- profiling high-polygon-density scenes and choosing a spatial acceleration structure.

Do not claim that game sound, full Wavetracing or Windows drop-in deployment has already passed.
