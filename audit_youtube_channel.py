import urllib.request, xml.etree.ElementTree as ET, json
ch="UCzALgHf_JmgbyDUnixxhp9A"
out={"channel_id":ch,"source":"YouTube Atom feed","items":[]}
url="https://www.youtube.com/feeds/videos.xml?channel_id="+ch
try:
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; channel-audit/1.0)"})
 with urllib.request.urlopen(req,timeout=30) as resp:
  xml=resp.read()
  print("RSS STATUS:",resp.status,"LENGTH:",len(xml))
 root=ET.fromstring(xml)
 atom="{http://www.w3.org/2005/Atom}"
 yt="{http://www.youtube.com/xml/schemas/2015}"
 out["title"]=root.findtext(atom+"title")
 for ent in root.findall(atom+"entry"):
  out["items"].append({"title":ent.findtext(atom+"title"),"videoId":ent.findtext(yt+"videoId"),"date":ent.findtext(atom+"published")})
except Exception as exc:
 out["error"]=str(exc)
print(json.dumps(out,ensure_ascii=False,indent=2))
open("channel_audit.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=2))
