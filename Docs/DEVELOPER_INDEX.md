# Developer guide — Aufake3D v0.9.2

Start with the [project README](../README.md), [current build/release guide](BUILD_AND_RELEASE.md) and [compatibility matrix](COMPATIBILITY.md). **Compiled outputs are under `dist/`, never inferred from source file names or old runtime ZIPs.** This index links to the detailed implementation contracts that are still useful; it is not a second set of install instructions.

## Engine and interfaces

| Subsystem | Authoritative technical notes |
|---|---|
| Overall source layout, call flow and ownership | [Source architecture](SOURCE_ARCHITECTURE.md) · [Source function guide](SOURCE_FUNCTION_GUIDE.md) |
| A3D COM interface contracts, ABI and lifetime | [COM ABI and lifetimes](COM_ABI_AND_LIFETIMES.md) |
| WaveOut worker, queue and polling | [WaveOut worker contract](WAVEOUT_WORKER_CONTRACT.md) |
| PCM buffers, positioning and source lifetimes | [PCM/spatial pipeline](PCM_AND_SPATIAL_PIPELINE.md) |
| HRTF, materials and reflection/occlusion work | [Geometry and HRTF](GEOMETRY_AND_HRTF.md) · [AU8830 modes](AU8830_HRTF_PERFORMANCE_MODES.md) |
| Alice provider and Miles compatibility | [Miles proxy and games](MILES_PROXY_AND_GAMES.md) |
| Source contributions and annotation policy | [Documentation policy](DOCUMENTATION_POLICY.md) |

## Experimental work

| Area | More detail |
|---|---|
| **Retail Descent 3** | [Public retail ZIP and evidence](DESCENT3_PUBLIC_RELEASE.md) · [COM contract probe](DESCENT3_A3D_API_PROBE.md) |
| **Descent 3 source engine** | [Standalone adapter build](DESCENT3_EXPERIMENTAL_BINARY_BUILD.md) · [integration notes](../Integrations/Descent3_Source/README.md) |
| RtCW geometry extraction (not sound activation) | [BSP exporter research](RTCW_BSP_EXPORT_V092.md) |
| GTA III/Vice City experiments | [GTA research](GTA_III_VICE_CITY_EXPERIMENTAL.md) |
| Game validation and scope | [Compatibility](COMPATIBILITY.md) |

The source-engine Descent 3 `.obj` is **not** a retail-game DLL or linked source-engine binary. The public retail ZIP uses copies of the existing shared core. Do not conflate its preliminary successful audio-load test with verified wave tracing or accurate HRTF.

## Build, correctness and audit

| Topic | Documentation |
|---|---|
| Pinned local build and three-way verification | [Build and release](BUILD_AND_RELEASE.md) · [One-click help](ONE_CLICK_BUILD.md) |
| Five-platform bit identity | [Cross-platform reproducibility](CROSS_PLATFORM_REPRODUCIBILITY.md) |
| Game kit files / COM setup | [Installation](INSTALLATION.md) · [Troubleshooting](TROUBLESHOOTING.md) |
| Security of launchers, proxies, release contents | [Binary security](BINARY_COMPONENTS_AND_SECURITY.md) · [Security review](SECURITY_REVIEW_V0814_RC1.md) |
| License/provenance boundaries | [Licensing audit](LICENSING_AUDIT.md) · [Third-party notices](../THIRD_PARTY_NOTICES.md) |
| Historical hotfixes / previous notes | [History index](HISTORY_INDEX.md) |

When touching a public ABI, realtime audio code or game adapter, preserve the contract comments, add a focused regression, and update the **current** guide. Historical experiments should remain in the archive without being presented as current installation instructions.
