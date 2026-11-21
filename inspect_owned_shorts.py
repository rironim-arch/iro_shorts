import requests,json,subprocess,sys,re,traceback
from pathlib import Path
out=Path("youtube_channel_manifest.json")
channel="UCsnDatcyPI0XIo7JFu3Df6g"
sources={}
try:
 feed=requests.get("https://www.youtube.com/feeds/videos.xml",params={"channel_id":channel},timeout=25,headers={"User-Agent":"Mozilla/5.0"});feed.raise_for_status()
 import xml.etree.ElementTree as ET
 ns={"atom":"http://www.w3.org/2005/Atom","yt":"http://www.youtube.com/xml/schemas/2015"}
 root=ET.fromstring(feed.text)
 sources["feed"]=[{"videoId":e.findtext("yt:videoId",namespaces=ns),
  "title":e.findtext("atom:title",namespaces=ns)} for e in root.findall("atom:entry",ns)]
except Exception as e:print("FEED_FETCH_ERROR",str(e)[:500],flush=True)
try:
 cmd=[sys.executable,"-m","yt_dlp","--flat-playlist","--playlist-items","1:40","--dump-single-json",
 "--no-warnings","--socket-timeout","15","--retries","1",
 f"https://www.youtube.com/channel/{channel}/shorts"]
 res=subprocess.run(cmd,text=True,capture_output=True,timeout=90)
 print("YTDLP_RETURN",res.returncode,"stderr",res.stderr[-1600:],flush=True)
 if res.returncode==0:
  data=json.loads(res.stdout)
  sources["shorts"]=[{"videoId":e.get("id"),"title":e.get("title"),
    "duration":e.get("duration"),"url":e.get("url")} for e in data.get("entries",[]) if e]
except Exception as e:print("YT_DLP_ERROR",repr(e),flush=True)
out.write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding="utf8")
for k,v in sources.items():
 print("FOUND",k,len(v),flush=True)
 for e in v:print("ITEM",k,e.get("videoId"),e.get("title"),flush=True)
if not any(sources.values()):raise RuntimeError("Could not fetch public channel feed or Shorts listing")
