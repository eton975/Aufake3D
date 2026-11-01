/* Half-Life retail 1.0.1.1 only: identify the optional Aureal splash-setting
 * routine before touching child RAM. Metadata alone is never sufficient.
 * This helper is platform independent so mismatches can be tested directly. */
static int hl_splash_signature(const unsigned char *pe,const unsigned char *code,
                               const unsigned char *names){
 static const unsigned char head[]={0x55,0x8b,0xec,0x83,0xec,0x10,0x53,0x56,0x57,0x89,0x4d,0xf0};
 static const unsigned char tail[]={0xb8,1,0,0,0,0xe9,0,0,0,0,0x5f,0x5e,0x5b,0xc9,0xc3};
 static const char strings[]="Software\\Aureal\\A3D\0SplashScreen";
 unsigned i;
 if(pe[0]!='P'||pe[1]!='E'||pe[2]||pe[3]||pe[4]!=0x4c||pe[5]!=1||pe[24]!=0x0b||pe[25]!=1)return 0;
 #define HL_U32(p) ((unsigned)(p)[0]|((unsigned)(p)[1]<<8)|((unsigned)(p)[2]<<16)|((unsigned)(p)[3]<<24))
 if(HL_U32(pe+8)!=0x3749e58au||HL_U32(pe+40)!=0x7e5c0u||HL_U32(pe+80)!=0x12c000u)return 0;
 #undef HL_U32
 for(i=0;i<sizeof(head);i++)if(code[i]!=head[i])return 0;
 for(i=0;i<sizeof(tail);i++)if(code[113+i]!=tail[i])return 0;
 for(i=0;i<sizeof(strings);i++)if(names[i]!=(unsigned char)strings[i])return 0;
 /* RegCreateKeyExA failure branch and the four-byte REG_DWORD write. */
 if(code[43]!=0xff||code[44]!=0x15||code[49]!=0x85||code[50]!=0xc0||code[51]!=0x0f||code[52]!=0x84)return 0;
 return 1;
}
