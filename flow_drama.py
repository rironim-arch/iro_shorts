"""Local Google Flow drama bridge (unofficial MCP, not Google API).
Run on the PC where your trusted Flow MCP is installed and Chrome is logged in.
Requirements: Python 3.11+, pip install mcp, FFmpeg with libass, Korean font.
Supply the installed MCP's JavaScript entry point via --server (no auto-install).
Examples (from the repository root):
  python flow_drama.py check --server C:/path/to/google-flow-mcp/dist/cli.js
  python flow_drama.py prepare --server C:/path/to/google-flow-mcp/dist/cli.js --project "https://flow.google.com/project/..."
  python flow_drama.py seed --server ... --project ... --confirm
  python flow_drama.py extend --server ... --confirm
  python flow_drama.py render
Use --resume instead of --confirm after a render timeout. Do not rerun a paid seed.
Outputs and state stay in ~/.iro_flow_drama/ep01, not in the public GitHub repo.
Before rendering, listen to both clips and correct captions.ass timing/text if needed.
"""
import argparse
import asyncio
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

SEED = """8초, 9:16 실제 한국 드라마. 고급 한식당. 낡은 회색 점퍼를 입은 백발 70대 남성과 검은 앞치마를 입은 50대 여성. 여성은 무시하듯 '할아버지, 여기 비싼데 돈은 있으세요?' 남성은 차분하게 '밥 한 끼 먹으려고요.' 자연스러운 한국어 생활 연기, 호흡, 정확한 입모양. 대사 겹침 없이. 마지막은 두 사람을 담는 중간 샷. 자막, 음악, 나레이션 없음."""
EXTEND = """7초 연속 장면. 같은 식당, 동일한 백발 노인의 회색 점퍼와 여성의 검은 앞치마, 얼굴과 음색을 유지. 정장 차림 40대 남성이 들어와 '회장님, 건물 인수 끝났습니다.' 노인이 차분하고 단호하게 '이 식당은 계약 연장하지 말게.' 여성의 놀란 표정으로 종료. 자연스러운 한국어 발음, 입모양, 현장음. 자막, 음악, 나레이션 없음."""
CAPTIONS = [(0.4, 4.1, "할아버지, 여기 비싼데\\N돈은 있으세요?", False),
            (4.5, 7.6, "밥 한 끼 먹으려고요.", False),
            (8.2, 11.0, "회장님,\\N건물 인수 끝났습니다.", True),
            (11.2, 14.4, "이 식당은\\N계약 연장하지 말게.", True)]

def write_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)

def timecode(seconds):
    cs = round(seconds * 100)
    return f"{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}"

def make_captions(path):
    if path.exists():
        return
    font = "Malgun Gothic" if os.name == "nt" else "Noto Sans CJK KR"
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font},104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,85,85,510,1
Style: Key,{font},104,&H0000E8FF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,0,2,85,85,510,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [f"Dialogue: 0,{timecode(a)},{timecode(b)},{'Key' if key else 'Main'},,0,0,0,,{t}" for a,b,t,key in CAPTIONS]
    path.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")

async def flow(args, folder, state, state_file):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    if not args.server:
        raise SystemExit("--server must point to the installed, trusted MCP entry point.")
    server = Path(args.server).expanduser().resolve(strict=True)
    params = StdioServerParameters(command="node", args=[str(server)]) if server.suffix in (".js", ".mjs", ".cjs") else StdioServerParameters(command=str(server), args=[])
    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=timedelta(minutes=35)) as session:
            await session.initialize()
            available = {tool.name for tool in (await session.list_tools()).tools}
            async def call(name, data):
                if name not in available:
                    raise RuntimeError("Installed MCP does not expose " + name)
                result = await session.call_tool(name, data)
                blocks = [b.text for b in result.content if b.type == "text"]
                value = result.structuredContent or json.loads(blocks[0])
                if result.isError or not value.get("ok"):
                    raise RuntimeError(str(value))
                return value
            conn = await call("flow_connect", {})
            if args.mode == "check":
                print(json.dumps({"logged_in": conn.get("logged_in"), "tools": sorted(available)}, ensure_ascii=False))
                return
            if not conn.get("logged_in"):
                raise SystemExit("Sign in to Google in the dedicated Chrome window, then run check again.")
            project = args.project or state.get("project")
            url = urlsplit(project or "")
            if url.scheme != "https" or url.hostname not in ("flow.google.com", "labs.google") or "/project/" not in url.path:
                raise SystemExit("Supply a real Google Flow project URL with --project.")
            if state.get("project") and state["project"] != project:
                raise SystemExit("Use a different --folder for a different project.")
            state["project"] = project
            write_json(state_file, state)
            if args.mode in ("prepare", "seed"):
                if state.get("seed"):
                    raise SystemExit("Seed already exists. Do not generate it twice.")
                if args.mode == "seed" and not (args.confirm or args.resume):
                    raise SystemExit("Run prepare first, then seed --confirm to spend credits.")
                if args.mode == "seed" and state.get("seed_submitted") and not args.resume:
                    raise SystemExit("Previous seed attempt recorded. Use --resume, not a second paid submit.")
                if args.mode == "seed" and not args.resume:
                    state["seed_submitted"] = True
                    write_json(state_file, state)
                result = await call("flow_generate_video", {"prompt": SEED, "model": args.model, "ratio":"9:16", "duration":8, "reference_images":[], "project_url":project, "output_dir":str(folder), "auto_confirm":args.mode=="seed" and args.confirm, "resume":args.resume, "edit_mode":False})
                if result.get("status") == "completed":
                    state.update(seed=result["files"][0], media_id=result["media_ids"][0])
                    write_json(state_file, state)
                print(json.dumps(result, ensure_ascii=False))
                return
            if not state.get("seed"):
                raise SystemExit("Complete the seed first.")
            if state.get("hop"):
                raise SystemExit("Extension already exists. Run render.")
            if not state.get("scene_url"):
                scene = await call("flow_scene_add", {"project_url":project,"media_id":state["media_id"]})
                state["scene_url"] = scene["scene_url"]
                write_json(state_file,state)
            if state.get("hop_submitted") and not args.resume:
                raise SystemExit("Previous extension recorded. Use --resume.")
            if args.confirm:
                state["hop_submitted"] = True
                write_json(state_file,state)
            result = await call("flow_scene_extend", {"scene_url":state["scene_url"],"prompt":EXTEND,"after_clip_index":0,"output_dir":str(folder),"auto_confirm":args.confirm,"resume":args.resume})
            if result.get("file"):
                state["hop"] = result["file"]
                write_json(state_file,state)
            print(json.dumps(result, ensure_ascii=False))

def render(folder, state):
    seed, hop = (Path(state[key]).resolve(strict=True) for key in ("seed", "hop"))
    make_captions(folder / "captions.ass")
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,setsar=1,format=yuv420p,setpts=PTS-STARTPTS"
    af = "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,asetpts=PTS-STARTPTS"
    graph = f"[0:v]{vf}[v0];[1:v]{vf}[v1];[0:a]{af}[a0];[1:a]{af}[a1];[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a];[v]ass=captions.ass[out]"
    subprocess.run(["ffmpeg","-n","-i",str(seed),"-i",str(hop),"-filter_complex",graph,"-map","[out]","-map","[a]","-t","15","-c:v","libx264","-crf","19","-c:a","aac","-b:a","160k","-movflags","+faststart","ep01_review.mp4"],cwd=folder,check=True)
    print("Review native dialogue and subtitle sync before publishing:", folder / "ep01_review.mp4")

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode",choices=["check","prepare","seed","extend","render"])
    p.add_argument("--server")
    p.add_argument("--project")
    p.add_argument("--model",choices=["veo-3.1-lite","veo-3.1-fast","veo-3.1-quality"],default="veo-3.1-quality")
    p.add_argument("--folder",type=Path,default=Path.home()/".iro_flow_drama"/"ep01")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--confirm",action="store_true")
    group.add_argument("--resume",action="store_true")
    args = p.parse_args()
    if args.mode in ("check","prepare","render") and (args.confirm or args.resume):
        p.error("This mode cannot spend credits or resume a generation.")
    folder = args.folder.expanduser().resolve()
    folder.mkdir(parents=True,exist_ok=True)
    state_file = folder/"state.json"
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    if args.mode == "render":
        if not all(state.get(k) for k in ("seed","hop")):
            p.error("Both completed Flow clips are required.")
        render(folder,state)
    else:
        asyncio.run(flow(args,folder,state,state_file))

if __name__ == "__main__":
    main()
