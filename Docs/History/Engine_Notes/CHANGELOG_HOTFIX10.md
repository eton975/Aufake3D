# Hotfix 10 changelog

- Fixed IA3dList::End / Call documented success return values: polygon count rather than S_OK.
- Fixed Quake III 1.17 0xABABABAB sentinel crash when no polygon-count progress was made.
- Added polygon accounting for quads separate from HRTF acoustic triangles.
- Added native polygon-count/vtable regression.
- Inherited Hotfix 9 (Hotfix 7 lineage), not Hotfix 8 experimental PCM tails.
