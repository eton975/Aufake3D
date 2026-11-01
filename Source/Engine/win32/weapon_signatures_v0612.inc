/* Exact FNV-1a matching deliberately prefers missed weapons to broad guesses.
 * The table has 15 buffer fingerprints for 14 names (two charge variants).
 * A group value is classification metadata, not a gain. Hash collisions are
 * possible; this heuristic does not identify all weapons or all game editions.
 */
/* v0.6.12 metadata-only known-weapon fingerprint index. */
/* Generated from two user-recorded v0.6.11 capture reports; 4KiB FNV1a hashes, NOT audio. */
/* Recognition is exact and deliberately conservative. False negatives are possible. */
typedef struct { unsigned hash; unsigned group; } A3DWeaponHash;
static const A3DWeaponHash a3d_known_weapons[]={
 {0x1f031e9cu,1u}, /* weapon_reappear.wav */
 {0x3669b959u,1u}, /* icewand_flesh1.wav */
 {0x39796204u,1u}, /* staff_explode1.wav */
 {0x3cc3d205u,1u}, /* jacks_ricochet1.wav */
 {0x58d63accu,1u}, /* icewand_flesh3.wav */
 {0x77eb8843u,1u}, /* explode1.wav */
 {0x913e81f6u,1u}, /* icewand_flesh2.wav */
 {0xa3df1f59u,1u}, /* icewand_world3.wav */
 {0xb1cff040u,1u}, /* staff_charge1.wav */
 {0xb967a411u,1u}, /* staff_liftoff.wav */
 {0xc428d666u,1u}, /* staff_charge1.wav */
 {0xca1bd8f6u,1u}, /* icewand_world1.wav */
 {0xe82fd879u,1u}, /* jacks_bounce.wav */
 {0xeb79dd0eu,1u}, /* jacks_toss.wav */
 {0xfe54789fu,1u}, /* staff_beam_loop.wav */
};
static unsigned a3d_weapon_is_known(unsigned hash){
 for(unsigned i=0;i<sizeof(a3d_known_weapons)/sizeof(a3d_known_weapons[0]);i++)
  if(a3d_known_weapons[i].hash==hash)return 1u;
 return 0u;
}
