# Linux and Wine setup — A3D v0.6.12

These are Windows PE32 binaries run through Wine on an x86-64 Linux desktop. No native Linux A3D library is included. ARM hosts and translation layers are outside this release's tested scope. Real Linux gameplay is unverified; the checks in VERIFICATION.md do not establish sound quality or frame pacing.

## 1. Install Wine

Use packages appropriate to one distribution and release; do not mix WineHQ and distribution libraries casually. Commands below are setup instructions for your Linux machine, not commands executed during this build.

For Debian 13 (Trixie) amd64 using Debian's conventional multiarch Wine packages:

```bash
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install wine wine32:i386 wine64 libwine:i386 fonts-wine
wine --version
```

For Ubuntu amd64 using distribution packages with conventional 32-bit support, enable i386 and update as above, then install wine and wine32:i386. If these have no installation candidate, check your Ubuntu release's enabled repositories and its Wine packaging instructions before proceeding. Package names and WoW64 policy vary by release. Do not apply the Debian package list to unrelated distributions.

Fedora: `sudo dnf install wine` installs Fedora's Wine meta-package and its dependencies. Check that this Wine can load the supplied PE32 self-test before installing game files. Do not assume a separate wine.i686 package is required by every Fedora release.

Arch: `sudo pacman -Syu wine` uses the current repository Wine. Arch transitioned to new WoW64 packaging, which runs 32-bit applications in a 64-bit prefix. Do not force WINEARCH=win32 with that build. Existing old 32-bit prefixes may need a fresh prefix and reinstallation of your game. Keep the old prefix as a backup.

Official distribution references consulted for this guide:

* https://wiki.debian.org/Wine
* https://ubuntu.com/project/docs/how-ubuntu-is-made/concepts/supported-architectures/
* https://packages.fedoraproject.org/pkgs/wine/wine/
* https://archlinux.org/news/transition-to-the-new-wow64-wine-and-wine-staging/
* https://wiki.archlinux.org/title/Wine

## 2. Select a prefix and install your game

Keep using the prefix where your game already works. In the terminal used for every following command, set its exact path:

```bash
export WINEPREFIX="$HOME/.local/share/wineprefixes/a3d-games"
wineboot -u
winecfg
```

This example creates/updates that prefix; replace it with your existing game's prefix when applicable. Let Wine select the default prefix architecture. Do not set WINEARCH on an existing prefix. A 64-bit WoW64 prefix can load 32-bit game programs when supported by its Wine installation. For a deliberately new conventional win32 prefix on Debian, WINEARCH=win32 is optional only when your installed Wine supports it.

Install your legally owned Windows games in that prefix using their installers, or use an existing properly installed and working game. Run the unmodified game once before adding A3D. Follow the game-version and VorpalFix requirements in WINDOWS_SETUP.md. Preserve required registry entries and original Miles/VorpalFix files; copying an isolated executable is insufficient.

## 3. Verify the extracted release and Wine ABI

Extract the archive to a normal user-writable directory. From Binaries:

```bash
sha256sum -c SHA256SUMS.txt
bash DEBIAN13_PREFLIGHT.sh
bash DEBIAN13_ABI_SMOKE.sh
```

The preflight is read-only; some dpkg checks are Debian-specific. On Fedora/Arch, use your package manager and the ABI smoke test instead of treating absent dpkg as an installation failure. The ABI smoke uses the included self-test and registration-free COM test. It needs no game. A pass proves only that those checks ran under your chosen Wine, not working game audio.

## 4. Copy and launch

Back up existing A3D DLLs, manifests and launchers. Copy the complete contents of the matching Binaries game folder into the directory containing the original game executable. Keep all game data, Miles files and VorpalFix winmm.dll. On a case-sensitive filesystem the launchers expect alice.exe or quake3.exe. If your original is Alice.exe and alice.exe does not already exist, create a link inside that directory with `ln -s Alice.exe alice.exe`. Check SndDrivers/mssa3d2.m3d spelling too. Do not overwrite the original executable to fix casing.

From the actual game directory, with the same WINEPREFIX:

```bash
bash ./RUN_A3D_WINE.sh
```

Using bash avoids depending on ZIP executable permissions. Paths with spaces are supported. Launchers preserve WINEPREFIX and other Wine settings. A3D_WINE_EXECUTABLE can select an executable path, for example `/opt/wine/bin/wine`; use a wrapper script if you need arguments. Do not put a whole command line in that variable.

The launchers select local native a3dapi/a3d DLLs and VorpalFix's native winmm for Alice 2011. Unrelated WINEDLLOVERRIDES entries are retained. Avoid conflicting duplicate overrides for these same DLL names. No regsvr32 or system-wide COM registration is needed.

Alice original-mix comparison: `bash ./RUN_A3D_ORIGINAL_MIX_WINE.sh`. Alice 2011 optional FPS request: `bash ./RUN_A3D_144FPS_WINE.sh`. Normal launch leaves FPS to VorpalFix. Extra game arguments are forwarded, for example `bash ./RUN_A3D_WINE.sh +set developer 1`.

## 5. Evaluate and troubleshoot

First confirm sound, directionality and stable playback. In both Alice versions compare clarity with the original mix in the same busy combat scene, especially Eye Staff charging. Listen for enemy/background balance as well as weapon audibility. For Quake III try a normal level and demo. Record distribution, wine --version, prefix type, audio server, game edition, launcher, and any crackling or frame pacing differences.

For crackling, compare Alice 2011's 4x512 or Quake III's 3x512 fallback. PipeWire/PulseAudio/ALSA and Wine add scheduling and buffering beyond the nominal 32 ms queue. For loader/COM failures, confirm that the ABI smoke passes in the same prefix, DLLs/manifests are adjacent, Wine supports PE32, and the game is the expected edition. A selector error must not be bypassed.

For bounded wrapper logs, run `bash ./RUN_A3D_DIAGNOSTIC_WINE.sh`, then exit normally. Wine's own stderr diagnostics are separate from A3D_LOG and may still appear. No real Wine executable is available on the Windows build host, so these launchers still require testing on your Linux system.

To uninstall, close the game, remove copied release files and restore backups. Keep the game, Miles components, VorpalFix and prefix. Do not delete your prefix as a routine troubleshooting step.
