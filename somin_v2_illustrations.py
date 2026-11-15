#!/usr/bin/env python3
"""Produce 48 STORY-SPECIFIC animated-film illustrations, not slides/overlaid text."""
import os,io,re,time,json,base64,random,traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from PIL import Image,ImageOps,ImageEnhance
from google import genai
from google.genai import types

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"somin_v2_art"
OUT.mkdir(exist_ok=True)
PLAN=json.loads((ROOT/"somin_v2_scene_plan.json").read_text(encoding="utf8"))
KEY=os.environ["GEMINI_API_KEY"]
MODEL=os.environ.get("GEMINI_IMAGE_MODEL","gemini-2.5-flash-image")
reference=base64.b64decode((ROOT/"somin_reference_face_260.jpg.b64").read_text().strip())
assert reference.startswith(b"\xff\xd8")
base_style=PLAN["style"]
characters=("Somin (the same leading woman as the supplied reference headshot), age 49 but graceful youthful oval face, pale skin, "
"large brown eyes, long straight deep-brown almost black hair, earth-tone coat or sweater; "
"her mother: Korean woman age 70, short wavy brown-gray hair, plum cardigan, proud manner; "
"father: Korean man age 75, short silver hair, slight posture; "
"younger brother: Korean man age 43, short neat dark hair; "
"Somin's son: Korean boy age about 12, short black hair. "
"Keep recurring cast recognizable, consistent hairstyle and clothes with the story timeline. "
"For the 1980s/1990s flashbacks younger Somin is visibly younger in a suitable era-accurate setting. ")
avoid=("No title typography, lettering, speech bubbles, story captions, logos, watermarks, split-panels, collage, "
"blurry photocopied slide, flat gradient poster, stock-photo aesthetic, or empty composition. "
"Make a full-bleed cinematic drama FRAME: physical scene with acting bodies, expressive gestures, carefully designed blocking, "
"clear environmental storytelling; painterly fine details and strong natural-looking cinematic light. "
"Emulate the premium Korean illustrated drama sample: painterly realistic animation and warm, believable faces.")
def save_asset(payload,out):
    pic=Image.open(io.BytesIO(payload)).convert("RGB")
    pic=ImageOps.fit(pic,(1600,900),method=Image.Resampling.LANCZOS,centering=(.5,.5))
    pic.save(out,quality=88,optimize=True)
    return out.stat().st_size

# A mother/daughter visual anchor is itself produced from the user's Somin face reference.
anchor=OUT/"characters.jpg"
if not anchor.exists():
    prompt=(f"{base_style}. {characters} {avoid} "
      "Character continuity image: Somin and her elderly mother sitting side by side on a Korean home sofa, "
      "both faces clearly visible, beautifully illustrated cinematic scene, Somin matches attached portrait exactly, "
      "mother wears muted burgundy sweater. No other people. 16:9.")
    c=genai.Client(api_key=KEY)
    response=c.models.generate_content(
        model=MODEL,
        contents=[types.Part.from_bytes(data=reference,mime_type="image/jpeg"),prompt],
        config=types.GenerateContentConfig(response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="16:9")))
    data=next((p.inline_data.data for p in response.candidates[0].content.parts
                 if getattr(p,"inline_data",None) and p.inline_data.data),None)
    if not data: raise RuntimeError("Could not generate character continuity image: stop; do not substitute PPT")
    save_asset(data,anchor)
    print("CHARACTERS_REFERENCE_READY",anchor.stat().st_size,flush=True)
mother_daughter=anchor.read_bytes()

def produce(chap,idx,description):
    out=OUT/f"scene_{chap:02}_{idx:02}.jpg"
    if out.exists() and out.stat().st_size>10000:return out.name
    prom=(f"{base_style}. {characters} {avoid}\n"
       f"This is dramatic storyboard chapter {chap}, shot {idx}. Exact scene to visually illustrate:\n{description}\n"
       "Match Somin and mother to the source portraits whenever those characters appear. "
       "Only characters physically present in this script beat should appear, "
       "not a parade of all character references. Wide 16:9 scene as a Korean 2D animated movie still, no text.")
    problems=[]
    for attempt in range(6):
        try:
            cli=genai.Client(api_key=KEY)
            ret=cli.models.generate_content(
              model=MODEL,
              contents=[
                 types.Part.from_bytes(data=reference,mime_type="image/jpeg"),
                 types.Part.from_bytes(data=mother_daughter,mime_type="image/jpeg"),
                 prom],
              config=types.GenerateContentConfig(
                 response_modalities=["IMAGE"],
                 image_config=types.ImageConfig(aspect_ratio="16:9")))
            data=next((p.inline_data.data for p in ret.candidates[0].content.parts
                       if getattr(p,"inline_data",None) and p.inline_data.data),None)
            if not data:raise RuntimeError("No image bytes returned")
            n=save_asset(data,out)
            if n<10000:raise RuntimeError("Scene image abnormally small")
            print("SCENE_READY",chap,idx,n,flush=True)
            return out.name
        except Exception as e:
            problems.append(str(e)[:200])
            print("SCENE_RETRY",chap,idx,attempt+1,problems[-1],flush=True)
            time.sleep(min(14*(attempt+1),90))
    raise RuntimeError(f"No illustration for {chap}:{idx}; {problems}")

shots=[(ch["number"],sh["index"],sh["description"]) for ch in PLAN["chapters"] for sh in ch["shots"]]
done=[];errors=[]
with ThreadPoolExecutor(max_workers=2) as pool:
    futs={pool.submit(produce,*shot):shot[:2] for shot in shots}
    for f in as_completed(futs):
        try:done.append(f.result())
        except Exception as e:
            errors.append(dict(shot=futs[f],error=str(e)))
(OUT/"scene_report.json").write_text(json.dumps({"total":len(shots),"rendered":len(done),
  "failed":errors,"scene_names":sorted(done)},ensure_ascii=False,indent=2),encoding="utf8")
if errors:raise RuntimeError("Missing genuine story illustrations; not replacing with slideshow gradients: "+str(errors))
print("ALL_SCENE_ILLUSTRATIONS_READY",len(done),flush=True)
