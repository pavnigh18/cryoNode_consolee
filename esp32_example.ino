// CryoNode packet encoder: same big-endian layout and CRC-16/CCITT as backend/packet.py.
#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>

uint16_t crc16(const uint8_t* d, size_t n){
  uint16_t c=0xFFFF;
  while(n--){c^=(uint16_t)(*d++)<<8; for(int i=0;i<8;i++) c=(c&0x8000)?(c<<1)^0x1021:c<<1;}
  return c;
}
void put16(uint8_t*&p,uint16_t v){*p++=v>>8;*p++=v;}
void put32(uint8_t*&p,uint32_t v){*p++=v>>24;*p++=v>>16;*p++=v>>8;*p++=v;}
void putS16(uint8_t*&p,int16_t v){put16(p,(uint16_t)v);}
String hexOf(const uint8_t* b,size_t n){String s; for(size_t i=0;i<n;i++){if(b[i]<16)s+="0";s+=String(b[i],HEX);} return s;}

void sendPacket(const char* url){
  uint8_t b[64],*p=b;
  *p++=0xC7; *p++=1; put16(p,1); put32(p,unixTime());
  put32(p,(int32_t)(-60.12345*1e5)); put32(p,(int32_t)(12.34567*1e5));
  putS16(p,(int16_t)(1.20*100)); put16(p,(uint16_t)(34.100*1000));
  put16(p,1200); put16(p,250); *p++=90; put16(p,180);
  put16(p,80); put16(p,270); putS16(p,-15); put16(p,9850);
  put16(p,12450); put16(p,700); putS16(p,30); *p++=-80; *p++=0;
  uint16_t c=crc16(b,p-b); put16(p,c);
  HTTPClient h; h.begin(url); h.addHeader("Content-Type","text/plain");
  h.POST(hexOf(b,p-b)); h.end();
}
