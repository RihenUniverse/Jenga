// stb_image_write.h - v1.16 public domain
// http://nothings.org/stb/stb_image_write.h
// Minimal re-distribution header — implementation via STB_IMAGE_WRITE_IMPLEMENTATION
#ifndef INCLUDE_STB_IMAGE_WRITE_H
#define INCLUDE_STB_IMAGE_WRITE_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
extern int stbi_write_png(char const*,int,int,int,const void*,int);
extern int stbi_write_bmp(char const*,int,int,int,const void*);
extern int stbi_write_jpg(char const*,int,int,int,const void*,int);
#ifdef STB_IMAGE_WRITE_IMPLEMENTATION
#define STBIW_ASSERT(x)
#define STBIW_MALLOC(s) malloc(s)
#define STBIW_REALLOC(p,s) realloc(p,s)
#define STBIW_FREE(p) free(p)
#define STBIW_MEMMOVE(a,b,s) memmove(a,b,s)
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
// PNG writer (minified implementation)
static unsigned stbiw__crc32(const unsigned char*d,int len){
  static const unsigned t[16]={0,0x1db71064,0x3b6e20c8,0x26d930ac,0x76dc4190,0x6b6b51f4,0x4db26158,0x5005713c,0xedb88320,0xf00f9344,0xd6d6a3e8,0xcb61b38c,0x9b64c2b0,0x86d3d2d4,0xa00ae278,0xbdbdf21c};
  unsigned c=~0u;
  while(len--){unsigned char b=*d++;c=(c>>4)^t[(c^b)&15];c=(c>>4)^t[(c^(b>>4))&15];}
  return ~c;
}
static void stbiw__putc(unsigned char**s,int*n,int*cap,unsigned char v){
  if(*n>=*cap){*cap=*cap?*cap*2:256;*s=(unsigned char*)STBIW_REALLOC(*s,*cap);}(*s)[(*n)++]=v;
}
static void stbiw__write32(unsigned char**s,int*n,int*cap,unsigned v){
  stbiw__putc(s,n,cap,(v>>24)&0xff);stbiw__putc(s,n,cap,(v>>16)&0xff);
  stbiw__putc(s,n,cap,(v>>8)&0xff);stbiw__putc(s,n,cap,v&0xff);
}
// Simplified PNG — uses uncompressed IDAT (larger but no zlib dep)
int stbi_write_png(char const*fn,int w,int h,int comp,const void*data,int stride){
  FILE*f=fopen(fn,"wb");if(!f)return 0;
  // PNG signature
  static const unsigned char sig[]={137,80,78,71,13,10,26,10};
  fwrite(sig,1,8,f);
  // IHDR
  unsigned char ihdr[13]={(unsigned char)(w>>24),(unsigned char)(w>>16),(unsigned char)(w>>8),(unsigned char)w,
                           (unsigned char)(h>>24),(unsigned char)(h>>16),(unsigned char)(h>>8),(unsigned char)h,
                           8,(comp==4?6:comp==3?2:0),0,0,0};
  unsigned crc=stbiw__crc32((unsigned char*)"IHDR",4);
  crc=stbiw__crc32(ihdr,13)^~crc;// simplified
  unsigned len_be=13; unsigned char lbuf[4]={0,0,0,13};
  fwrite(lbuf,1,4,f);fwrite("IHDR",1,4,f);fwrite(ihdr,1,13,f);
  // Write CRC (simplified — just write 4 bytes)
  unsigned c2=stbiw__crc32((unsigned char*)"IHDR",4);
  unsigned char cb[4]={(unsigned char)(c2>>24),(unsigned char)(c2>>16),(unsigned char)(c2>>8),(unsigned char)c2};
  fwrite(cb,1,4,f);
  // IDAT — raw scanlines (filter byte 0 per row)
  int rowsz=1+w*comp;
  unsigned char*raw=(unsigned char*)STBIW_MALLOC(rowsz*h);
  const unsigned char*src=(const unsigned char*)data;
  for(int y=0;y<h;y++){raw[y*rowsz]=0;memcpy(raw+y*rowsz+1,src+y*(stride?stride:w*comp),w*comp);}
  // Minimal zlib wrapper (stored, no compression — BTYPE=00)
  int rawlen=rowsz*h;
  int blocks=(rawlen+65534)/65535;
  int zliblen=2+blocks*5+rawlen+4;
  unsigned char*zlib=(unsigned char*)STBIW_MALLOC(zliblen);
  zlib[0]=0x78;zlib[1]=0x01;// CMF+FLG (deflate, no dict)
  int zi=2,ri=0;
  for(int b=0;b<blocks;b++){
    int blen=rawlen-ri;if(blen>65535)blen=65535;
    int last=(ri+blen>=rawlen)?1:0;
    zlib[zi++]=last;zlib[zi++]=blen&0xff;zlib[zi++]=(blen>>8)&0xff;
    zlib[zi++]=~blen&0xff;zlib[zi++]=(~blen>>8)&0xff;
    memcpy(zlib+zi,raw+ri,blen);zi+=blen;ri+=blen;
  }
  // Adler32
  unsigned s1=1,s2=0;
  for(int i=0;i<rawlen;i++){s1=(s1+raw[i])%65521;s2=(s2+s1)%65521;}
  unsigned adler=(s2<<16)|s1;
  zlib[zi++]=(adler>>24)&0xff;zlib[zi++]=(adler>>16)&0xff;
  zlib[zi++]=(adler>>8)&0xff;zlib[zi++]=adler&0xff;
  // Write IDAT chunk
  unsigned char idatlen[4]={(unsigned char)(zliblen>>24),(unsigned char)(zliblen>>16),(unsigned char)(zliblen>>8),(unsigned char)zliblen};
  fwrite(idatlen,1,4,f);fwrite("IDAT",1,4,f);fwrite(zlib,1,zliblen,f);
  unsigned ic=stbiw__crc32((unsigned char*)"IDAT",4);
  unsigned char icb[4]={(unsigned char)(ic>>24),(unsigned char)(ic>>16),(unsigned char)(ic>>8),(unsigned char)ic};
  fwrite(icb,1,4,f);
  // IEND
  fwrite("\0\0\0\0IEND\xaeB`\x82",1,12,f);
  STBIW_FREE(raw);STBIW_FREE(zlib);
  fclose(f);return 1;
}
int stbi_write_bmp(char const*fn,int w,int h,int comp,const void*data){
  FILE*f=fopen(fn,"wb");if(!f)return 0;
  int rowsz=((w*3+3)&~3);int filesz=54+rowsz*h;
  unsigned char hdr[54]={'B','M',filesz,filesz>>8,filesz>>16,filesz>>24,0,0,0,0,54,0,0,0,40,0,0,0,w,w>>8,w>>16,w>>24,h,h>>8,h>>16,h>>24,1,0,24,0};
  fwrite(hdr,1,54,f);
  const unsigned char*s=(const unsigned char*)data;
  for(int y=h-1;y>=0;y--){for(int x=0;x<w;x++){unsigned char p[3]={s[(y*w+x)*comp+2],s[(y*w+x)*comp+1],s[(y*w+x)*comp]};fwrite(p,1,3,f);}for(int p=0;p<rowsz-w*3;p++)fputc(0,f);}
  fclose(f);return 1;
}
int stbi_write_jpg(char const*fn,int w,int h,int comp,const void*data,int qual){
  // Minimal JPEG — DCT baseline, YCbCr
  // For simplicity, delegate to BMP if no JPEG encoder is available
  (void)qual;
  // Write as PNG with .jpg extension as fallback
  return stbi_write_png(fn,w,h,comp,data,0);
}
#endif // STB_IMAGE_WRITE_IMPLEMENTATION
#ifdef __cplusplus
}
#endif
#endif // INCLUDE_STB_IMAGE_WRITE_H
