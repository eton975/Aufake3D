# Security and responsible testing

Aufake3D is experimental software that loads into legacy game processes. Test only on copies of games you own. Make full backups before replacing any existing game-local DLL or manifest. Do not put `mss32.dll` proxies into system folders or use them with untrusted or multiplayer processes.

Avoid system-wide COM registration; use controlled application-local activation when possible. Historical launch helpers sometimes manipulate a **child process in memory**, even though they do not alter an EXE on disk. Inspect the source and game policy before using them. CI does not execute proprietary games or attempt to download original SDKs.

Reports may contain usernames or game install paths. Remove those before filing public issues. Do not attach credentials, CD keys, personal logs or proprietary media. For a vulnerability, open a private security report to the future repository maintainer rather than posting exploit material publicly.
