/* Common *untrusted input* parser for both candidate launchers.
 * This header deliberately has no Win32 API imports. It accepts exactly
 * "--game basename.exe -- [opaque game arguments]"; never a directory or
 * an absolute path. Neither launcher opens/patches original files on disk.
 */
#ifndef A3D_GENERIC_TARGET_H
#define A3D_GENERIC_TARGET_H
static const char *a3d_skip_space(const char *p) {
  while (*p==' ' || *p=='\t') ++p;
  return p;
}
static const char *a3d_own_args(const char *p) {
  if (*p=='"') {
    ++p; while (*p && *p!='"') ++p;
    if (*p) ++p;
  } else {
    while (*p && *p!=' ' && *p!='\t') ++p;
  }
  return a3d_skip_space(p);
}
#ifdef A3D_GENERIC
static const char *a3d_generic_target(const char **rest) {
  static char name[256];
  const char *p=*rest;
  const char *flag="--game";
  unsigned long n=0;
  while (*flag && *p==*flag) { ++p; ++flag; }
  if (*flag || (*p!=' ' && *p!='\t')) return 0;
  p=a3d_skip_space(p);
  int quoted=(*p=='"');
  if (quoted) ++p;
  while (*p && (quoted ? *p!='"' : (*p!=' ' && *p!='\t'))) {
    if (n>=sizeof(name)-1 || *p=='/' || *p=='\\' || *p==':' || *p=='"' ||
        *p=='<' || *p=='>' || *p=='|' || *p=='*' || *p=='?') return 0;
    name[n++]=*p++;
  }
  if (quoted) {
    if (*p!='"') return 0;
    ++p;
  }
  name[n]=0;
  if (n<5 || name[n-4]!='.' || ((name[n-3]|32)!='e') ||
      ((name[n-2]|32)!='x') || ((name[n-1]|32)!='e')) return 0;
  for (unsigned long i=0; i+1<n; i++)
    if (name[i]=='.' && name[i+1]=='.') return 0;
  p=a3d_skip_space(p);
  if (p[0]!='-' || p[1]!='-' || (p[2] && p[2]!=' ' && p[2]!='\t')) return 0;
  *rest=a3d_skip_space(p+2);
  return name;
}
#endif /* A3D_GENERIC */
#endif
