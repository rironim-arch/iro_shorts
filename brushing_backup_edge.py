"""Backup Korean TTS for original brushing Short when Gemini daily requests are blocked."""
import asyncio,os,json,subprocess
from pathlib import Path
import edge_tts
OUT=Path("output_brushing_edge");OUT.mkdir(exist_ok=True)
SCRIPTS=[
"칫솔질, 세게 문지르면 더 깨끗할까요? 사실 중요한 건 힘보다 방법입니다.",
"미국치과의사협회 권고에 따르면, 부드러운 칫솔을 잇몸 경계에 약 45도로 대세요. 세게 누르지 마세요.",
"칫솔은 짧고 부드럽게 앞뒤로 움직이고, 치아 바깥쪽과 안쪽, 씹는 면까지 모두 닦습니다.",
"앞니 안쪽은 칫솔을 세워 위아래로 움직이세요. 불소치약으로 하루 두 번, 한 번에 약 2분입니다.",
"그리고 의외의 포인트! 양치 후 치약은 뱉되, 곧바로 물로 여러 번 헹구지 않는 편이 불소 보호에 유리합니다.",
"칫솔이 닿지 않는 치아 사이는 치실이나 치간칫솔로 하루 한 번 닦아주세요.",
"오늘부터 바꿔보세요! 도움이 됐다면 좋아요와 구독! 생활알고리즘, 알아두면 쓸모 있는 생활상식."
]
async def main():
    timing=[]
    for i,line in enumerate(SCRIPTS):
        path=OUT/f"scene_{i:02d}.mp3"
        for attempt in range(3):
            try:
                await edge_tts.Communicate(line,voice="ko-KR-HyunsuMultilingualNeural",rate="+0%").save(str(path))
                if path.stat().st_size<1500:raise RuntimeError("Unexpectedly small Edge audio")
                break
            except Exception:
                if attempt>=2:raise
                await asyncio.sleep(3+attempt*4)
        wav=OUT/f"scene_{i:02d}.wav"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(path),"-ac","1","-ar","24000",str(wav)],check=True)
        d=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(wav)],text=True).strip())
        timing.append({"scene":i,"text":line,"duration":d})
        print(f"scene {i+1}/7: {d:.2f}s",flush=True)
    (OUT/"script.json").write_text(json.dumps(timing,ensure_ascii=False,indent=2),encoding="utf-8")
asyncio.run(main())
