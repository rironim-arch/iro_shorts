"""Read-only cross-post source test for a public video belonging to connected user's YouTube channel."""
import subprocess,json, pathlib, os, sys
url="https://www.youtube.com/watch?v=qzBykqwGAaM"
out=pathlib.Path("ig_staging_test")
out.mkdir(exist_ok=True)
cmd=["yt-dlp","--no-playlist","--no-warnings","--socket-timeout","15","--retries","1","--fragment-retries","1","-f","b[ext=mp4]/bv*[ext=mp4]+ba[ext=m4a]/b","--merge-output-format","mp4","-o",str(out/"%(id)s.%(ext)s"),url]
try:
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=120)
 report={"url":url,"returncode":p.returncode,"log":p.stdout[-4000:],"files":[{"name":f.name,"size":f.stat().st_size} for f in out.glob("*")]}
except Exception as e:
 report={"url":url,"error":str(e)}
print(json.dumps(report,ensure_ascii=False))
pathlib.Path("ig_staging_test.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
