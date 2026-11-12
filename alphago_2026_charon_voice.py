"""AlphaGo 2016 versus AI 2026: original Gemini Charon Korean narration.
One exact line per audio segment for truthful subtitle sync. No social posting.
"""
from pathlib import Path
import os,asyncio,wave,json,subprocess
from gemini_charon_tts import speech

OUT=Path("out_alphago_2026_voice");OUT.mkdir(exist_ok=True)
SCENES=[
{"heading":"2016년, 전 세계가 놀랐다","caption":"이세돌 vs 알파고 4대 1","say":"2016년, 세계를 놀라게 한 바둑 대결. 알파고는 이세돌 9단을 상대로 4대 1로 승리했습니다."},
{"heading":"하지만 한 분야의 천재","caption":"알파고는 바둑 특화 AI","say":"하지만 당시 알파고는 바둑에 특화된 인공지능이었어요. 자유롭게 대화하거나 글을 쓰는 시스템은 아니었죠."},
{"heading":"그리고 10년이 흐른 지금","caption":"2026년, 무엇이 달라졌을까?","say":"그로부터 10년. 지금의 인공지능은 사람과 대화하고, 글을 쓰고, 사진과 음성까지 이해합니다."},
{"heading":"이제는 일도 도와준다","caption":"코딩 · 문서 분석 · 작업 계획","say":"프로그램 코드를 작성하고 오류를 찾거나, 복잡한 문서를 정리하고 작업 계획을 세우기도 해요."},
{"heading":"수학도 세계 최고 수준?","caption":"국제수학올림피아드 금메달 수준","say":"2025년, 구글의 제미나이 딥 씽크는 국제수학올림피아드에서 금메달 수준인 35점을 기록했습니다."},
{"heading":"그럼 인간을 완전히 넘어섰을까?","caption":"모든 분야에서 똑똑할까?","say":"그렇다면 지금의 인공지능은 사람보다 모든 면에서 똑똑할까요? 놀랍게도, 그렇지는 않습니다."},
{"heading":"뜻밖의 약점","caption":"아날로그 시계 읽기 약 50%","say":"스탠퍼드의 2026년 인공지능 지수에 따르면, 최상위 모델의 아날로그 시계 읽기 정답률은 약 50퍼센트였습니다."},
{"heading":"컴퓨터를 직접 조작해도","caption":"작업 성공률 약 66%","say":"컴퓨터를 조작하는 인공지능도 정해진 평가에서 작업 성공률이 약 66퍼센트였어요. 세 번 중 한 번은 실패한 셈이죠."},
{"heading":"알파고와 현재 AI의 차이","caption":"한 분야의 강자 → 다재다능한 조력자","say":"알파고가 바둑이라는 한 분야의 강자였다면, 지금의 인공지능은 수많은 분야를 넘나들고 있습니다."},
{"heading":"하지만 검증은 필수","caption":"그럴듯하게 틀릴 수 있다","say":"하지만 그럴듯하게 틀린 답을 하거나, 복잡한 현실 상황에서 실수할 수도 있어요."},
{"heading":"10년의 가장 큰 변화","caption":"지능의 배수보다 능력의 범위","say":"핵심은 몇 배 더 똑똑해졌느냐가 아닙니다. 바둑만 잘하던 인공지능이 여러 일을 돕는 존재로 바뀌었다는 거죠."},
{"heading":"앞으로 10년 뒤는?","caption":"당신의 생각은? 구독 · 좋아요","say":"여러분은 앞으로 10년 뒤, 인공지능이 어디까지 발전할 것 같나요? 생활알고리즘! 유익했다면 구독과 좋아요!"}
]

async def main():
    manifest=[]
    for i,scene in enumerate(SCENES):
        raw=OUT/f"voice_{i:02d}_raw.wav"
        processed=OUT/f"voice_{i:02d}.wav"
        await speech(scene["say"],raw)
        subprocess.run(["ffmpeg","-y","-hide_banner","-loglevel","error","-i",str(raw),"-af","atempo=1.25","-ar","24000","-ac","1",str(processed)],check=True)
        with wave.open(str(processed),"rb") as w:
            length=w.getnframes()/w.getframerate()
        if length<1 or length>30: raise RuntimeError(f"Unexpected audio duration scene={i}: {length}")
        manifest.append({"scene":i,**scene,"audio":processed.name,"duration":length})
        print("CHARON_SCENE",i,"SECONDS",round(length,3),flush=True)
        await asyncio.sleep(1)
    (OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
    total=sum(s["duration"] for s in manifest)
    print("TOTAL_SPEECH_SECONDS",round(total,3),flush=True)
if __name__=="__main__":asyncio.run(main())
