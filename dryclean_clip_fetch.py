"""Download actual-motion footage from Pexels for drycleaning educational illustrations."""
from pathlib import Path
import requests,subprocess,imageio_ffmpeg
D=Path("dryclean_clips");D.mkdir(exist_ok=True)
F=imageio_ffmpeg.get_ffmpeg_exe()
S=requests.Session();S.headers["User-Agent"]="Mozilla/5.0"
VIDEOS=[
(8756699,"commercial_laundry_workers",4096,2160,25),
(8756703,"laundry_worker",2160,4096,25),
(8756886,"garment_loading",2160,4096,25),
(8756891,"rotating_clothes",4096,2160,25),
(10558374,"garment_steaming",2160,4096,25),
(36302138,"tailor_steam_press",1080,1920,60),
(5592521,"laundry_detergent_hand",1920,1080,25),
(5592516,"laundry_machine",1920,1080,25),
(6843718,"fabric_handwashing",1920,1080,25),
]
def options(id,native_w,native_h,fps):
   ratio=native_w/native_h
   variants=[]
   for width in (540,720,960,1080,1280,1920):
      h=round(width/ratio)
      if h%2:h+=1
      variants.append((width,h))
   variants+= [(540,960),(960,540),(720,1280),(1280,720),(1080,1920),(1920,1080),(720,1366),(1080,2048),(540,1024),(1920,1012)]
   urls=[]
   for x,y in variants:
      for fr in (fps,25,30,24):
         urls.append(f"https://videos.pexels.com/video-files/{id}/{id}-hd_{x}_{y}_{fr}fps.mp4")
   urls.append(f"https://www.pexels.com/download/video/{id}/")
   # Ensure unique
   return list(dict.fromkeys(urls))
def fetch(id,name,w,h,fps):
  print("LOOKUP",name,id,flush=True)
  src=D/f"raw_{id}.mp4"
  ulist=options(id,w,h,fps)
  for ix,u in enumerate(ulist):
    try:
      q=S.head(u,timeout=3,allow_redirects=True)
      if q.status_code!=200:continue
      clen=int(q.headers.get("Content-Length","0"))
      ctype=q.headers.get("Content-Type","")
      if not ("video" in ctype or "octet" in ctype):continue
      print("AVAILABLE",id,u,q.url,'bytes',clen,flush=True)
      if clen > 70000000:continue
      with S.get(u,stream=True,timeout=(5,40)) as r:
          r.raise_for_status()
          with src.open("wb") as file:
              n=0
              for b in r.iter_content(524288):
                 if b:
                    n+=len(b)
                    if n>70000000:raise RuntimeError("Too large")
                    file.write(b)
      if src.stat().st_size < 30000:continue
      output=D/f"clip_{name}.mp4"
      subprocess.run([F,"-y","-hide_banner","-loglevel","error","-i",str(src),
        "-t","8","-vf","scale=960:960:force_original_aspect_ratio=increase,crop=960:960,fps=20,format=yuv420p",
        "-an","-c:v","libx264","-crf","27","-preset","veryfast",str(output)],
        check=True,timeout=130)
      print("READY",name,output.stat().st_size,flush=True)
      src.unlink(missing_ok=True)
      return True
    except Exception as e:
      if ix%16==0:print("RETRY",id,ix,str(e)[:100],flush=True)
      src.unlink(missing_ok=True)
  print("UNAVAILABLE",name,flush=True)
  return False
def main():
  results={}
  for id,name,w,h,fps in VIDEOS:
    results[name]=fetch(id,name,w,h,fps)
  print("CLIPS_RESULT",results,flush=True)
  (D/"status.txt").write_text(str(results),encoding="utf-8")
if __name__=="__main__":main()
