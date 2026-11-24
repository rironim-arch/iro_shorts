import os,sys,subprocess,json,time
from pathlib import Path
root=Path("nabi_recovered")
root.mkdir(exist_ok=True)
ids=[int(x) for x in os.environ["NABI_IDS"].split(",")]
records=[]
failed=[]
for i in ids:
    p=root/f"clip_{i:03d}"
    for attempt in range(2):
        env=dict(os.environ,NABI_RANGE=f"{i}-{i}",NABI_OUT=str(p))
        try:
            print("CLIP START",i,attempt+1,flush=True)
            subprocess.run([sys.executable,"-u","nabi_longform_isolated_clip.py"],env=env,check=True,timeout=120)
            m=json.loads((p/"manifest.json").read_text(encoding="utf-8"))
            assert m["complete"] and len(m["clips"])==1
            rec=m["clips"][0]
            assert rec["i"]==i and (p/rec["file"]).is_file()
            records.append(rec)
            break
        except (subprocess.TimeoutExpired,subprocess.CalledProcessError,ValueError,AssertionError,OSError) as e:
            print("CLIP FAILED",i,type(e).__name__,str(e)[:200],flush=True)
            if attempt==1: failed.append(i)
            else: time.sleep(8)
    (root/"batch_status.json").write_text(json.dumps({"passed":[r["i"] for r in records],"failed":failed}),encoding="utf-8")
print("BATCH DONE",len(records),failed,flush=True)
if failed:sys.exit(1)
