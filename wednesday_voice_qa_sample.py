from google import genai
from google.genai import types
import os,re,wave,subprocess,json
from pathlib import Path
out=Path("wednesday_voice_qa");out.mkdir(exist_ok=True)
text="남편은 세 달째 매주 수요일 밤마다 집을 나갔습니다. 볼일이 있다는 말뿐, 그 시간엔 전화도 받지 않았죠. 혹시 다른 여자가 생긴 걸까요?"
prompt=("아래 짧은 한국어 창작 감동사연을, 40대 한국 여성 전문 오디오북 내레이터가 "
"자기 경험을 회상하듯 한 사람의 차분하고 따뜻한 목소리로 읽어주세요. "
"실제 사람처럼 문장 끝을 자연스럽게 처리하고, 의심되는 부분은 걱정스러운 감정을 작게 담으세요. "
"과장하거나 뉴스 앵커처럼 읽지 말고, 추가 문장은 읽지 마세요.\n"
"원고:\n"+text)
(out/"script.txt").write_text(text,encoding="utf8")
client=genai.Client(api_key=os.environ["GEMINI_API_KEY"])
try:
    r=client.models.generate_content(
      model="gemini-2.5-pro-preview-tts",contents=prompt,
      config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
          voice_config=types.VoiceConfig(prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")))))
    pkt=next((p.inline_data for p in r.candidates[0].content.parts if getattr(p,"inline_data",None) and p.inline_data.data),None)
    if not pkt:raise RuntimeError("EMPTY_AUDIO_RESPONSE")
    raw=out/"original.wav"
    if pkt.data.startswith(b"RIFF"):raw.write_bytes(pkt.data)
    else:
        sample=re.search(r"rate=(\d+)",pkt.mime_type or "")
        with wave.open(str(raw),"wb") as w:
            w.setnchannels(1);w.setsampwidth(2);w.setframerate(int(sample.group(1)) if sample else 24000);w.writeframes(pkt.data)
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(raw),"-af","atempo=1.25,loudnorm=I=-17:TP=-2:LRA=10",
      "-ac","1","-ar","24000",str(out/"kore_pro_125.wav")],check=True)
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(out/"kore_pro_125.wav"),
      "-c:a","libmp3lame","-b:a","160k",str(out/"kore_pro_125.mp3")],check=True)
    with wave.open(str(out/"kore_pro_125.wav"),"rb") as w:
        seconds=round(w.getnframes()/w.getframerate(),1)
    print("VOICE_SAMPLE_OK",json.dumps({"duration_seconds":seconds,"model":"gemini-2.5-pro-preview-tts","voice":"Kore","speed":1.25},ensure_ascii=False),flush=True)
except Exception as e:
    print("VOICE_SAMPLE_FAILED_NO_RETRY",str(e)[:1200],flush=True)
    raise
