import json, os, re, subprocess, threading, wave, urllib.request
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from vosk import Model, KaldiRecognizer

APP=Path(__file__).resolve().parent; MODELS=APP/"models"
MODEL_DIRS={"Greek":MODELS/"greek","English":MODELS/"english"}
OLLAMA_URL="http://localhost:11434/api/generate"; OLLAMA_MODEL="llama3.2:3b"

class ClipForge(ctk.CTk):
 def __init__(self):
  super().__init__();self.title("ClipForge Desktop");self.geometry("980x760")
  self.video=ctk.StringVar();self.language=ctk.StringVar(value="Greek + English");self.output=ctk.StringVar();self.max_clips=ctk.IntVar(value=10);self.min_len=ctk.IntVar(value=8);self.max_len=ctk.IntVar(value=45);self.padding_before=ctk.IntVar(value=3);self.padding_after=ctk.IntVar(value=3);self.keep_audio=ctk.BooleanVar(value=False);self.ai_enabled=ctk.BooleanVar(value=True);self.cancel_event=threading.Event();self.last_output=None
  ctk.CTkLabel(self,text="ClipForge Desktop",font=ctk.CTkFont(size=26,weight="bold")).pack(pady=14)
  row=ctk.CTkFrame(self);row.pack(fill="x",padx=24,pady=6);ctk.CTkEntry(row,textvariable=self.video).pack(side="left",fill="x",expand=True,padx=8,pady=8);ctk.CTkButton(row,text="Choose video",command=self.choose).pack(side="right",padx=8)
  settings=ctk.CTkFrame(self);settings.pack(fill="x",padx=24,pady=6);ctk.CTkLabel(settings,text="Settings",font=ctk.CTkFont(size=16,weight="bold")).grid(row=0,column=0,columnspan=6,sticky="w",padx=12,pady=8)
  ctk.CTkLabel(settings,text="Language").grid(row=1,column=0,padx=8,pady=5,sticky="w");ctk.CTkOptionMenu(settings,variable=self.language,values=["Greek + English","Greek only","English only"]).grid(row=1,column=1,padx=8,pady=5,sticky="w")
  self.entry(settings,"Max clips",self.max_clips,1,2,3);self.entry(settings,"Min seconds",self.min_len,2,0,1);self.entry(settings,"Max seconds",self.max_len,2,2,3);self.entry(settings,"Padding before",self.padding_before,3,0,1);self.entry(settings,"Padding after",self.padding_after,3,2,3)
  ctk.CTkCheckBox(settings,text="Use Ollama AI scoring",variable=self.ai_enabled).grid(row=4,column=0,columnspan=2,padx=8,pady=8,sticky="w");ctk.CTkCheckBox(settings,text="Keep temporary WAV audio",variable=self.keep_audio).grid(row=4,column=2,columnspan=2,padx=8,pady=8,sticky="w")
  out=ctk.CTkFrame(self);out.pack(fill="x",padx=24,pady=6);ctk.CTkLabel(out,text="Output folder (optional)").pack(side="left",padx=8);ctk.CTkEntry(out,textvariable=self.output).pack(side="left",fill="x",expand=True,padx=8,pady=8);ctk.CTkButton(out,text="Choose folder",command=self.choose_output).pack(side="right",padx=8)
  controls=ctk.CTkFrame(self);controls.pack(fill="x",padx=24,pady=6);ctk.CTkButton(controls,text="Start",command=self.start).pack(side="left",padx=8,pady=8);ctk.CTkButton(controls,text="Cancel",command=self.cancel).pack(side="left",padx=8,pady=8);self.open_btn=ctk.CTkButton(controls,text="Open output folder",command=self.open_output,state="disabled");self.open_btn.pack(side="right",padx=8,pady=8)
  self.progress=ctk.CTkProgressBar(self);self.progress.pack(fill="x",padx=24,pady=10);self.progress.set(0);self.status=ctk.CTkLabel(self,text="Choose a video to begin.");self.status.pack(anchor="w",padx=24);self.log=ctk.CTkTextbox(self);self.log.pack(fill="both",expand=True,padx=24,pady=10)
 def entry(self,parent,label,var,row,col,entrycol):
  ctk.CTkLabel(parent,text=label).grid(row=row,column=col,padx=8,pady=5,sticky="w");ctk.CTkEntry(parent,textvariable=var,width=70).grid(row=row,column=entrycol,padx=8,pady=5,sticky="w")
 def choose(self):
  f=filedialog.askopenfilename(filetypes=[("Video files","*.mp4 *.mkv *.mov *.avi *.webm"),("All files","*.*")]);
  if f:self.video.set(f)
 def choose_output(self):
  d=filedialog.askdirectory();
  if d:self.output.set(d)
 def log_line(self,t):self.after(0,lambda:(self.log.insert("end",t+"\n"),self.log.see("end")))
 def update(self,t,v):self.after(0,lambda:(self.status.configure(text=t),self.progress.set(v)))
 def cancel(self):self.cancel_event.set();self.log_line("Cancellation requested...")
 def open_output(self):
  if self.last_output and self.last_output.exists():os.startfile(str(self.last_output))
 def read_settings(self):
  vals=[self.max_clips.get(),self.min_len.get(),self.max_len.get(),self.padding_before.get(),self.padding_after.get()]
  if not all(x>=0 for x in vals) or vals[0]<1 or vals[1]<1 or vals[2]<vals[1]:raise ValueError("Settings must be valid: clips >= 1, lengths > 0, and maximum >= minimum.")
  return vals
 def start(self):
  src=Path(self.video.get())
  if not src.exists():messagebox.showerror("ClipForge","Choose an existing video first.");return
  try:settings=self.read_settings()
  except Exception as e:messagebox.showerror("ClipForge",str(e));return
  self.cancel_event.clear();self.open_btn.configure(state="disabled");threading.Thread(target=self.process,args=(src,settings),daemon=True).start()
 def process(self,src,settings):
  maxclips,minlen,maxlen,padding_before,padding_after=settings;wav=src.with_suffix(".clipforge.wav");outdir=Path(self.output.get()) if self.output.get() else src.parent/"ClipForge_Output"
  try:
   self.update("Extracting audio...",.02);self.log_line("Extracting audio...");subprocess.run(["ffmpeg","-y","-i",str(src),"-vn","-ac","1","-ar","16000","-sample_fmt","s16",str(wav)],check=True,capture_output=True)
   selected=["Greek","English"] if self.language.get()=="Greek + English" else [self.language.get().replace(" only","")]
   for lang in selected:
    if not MODEL_DIRS[lang].exists():raise RuntimeError(f"Missing {lang} model: {MODEL_DIRS[lang]}")
   self.update("Loading Vosk models...",.05);models={lang:Model(str(MODEL_DIRS[lang])) for lang in selected};wf=wave.open(str(wav),"rb");rate=wf.getframerate();total=max(1,wf.getnframes());words=transcribe_windows(wf,models,selected,rate,total,self);wf.close()
   srt=src.with_suffix(".srt");write_srt(words,srt);self.log_line(f"Saved transcript: {srt}");self.update("Creating candidates...",.55);clips=make_candidates(words,minlen,maxlen,padding_before,padding_after)
   if self.ai_enabled.get():clips=score_candidates(clips,words,self)
   clips=clips[:maxclips];outdir.mkdir(parents=True,exist_ok=True);created=[]
   for i,item in enumerate(clips,1):
    if self.cancel_event.is_set():return
    start,end=item["start"],item["end"];target=outdir/f"clip_{i:03}.mp4";self.update(f"Exporting clip {i} of {len(clips)}...",.65+.3*i/max(1,len(clips)));subprocess.run(["ffmpeg","-y","-ss",f"{start:.3f}","-i",str(src),"-t",f"{end-start:.3f}","-map","0:v:0","-map","0:a:0?","-c:v","libx264","-preset","veryfast","-c:a","aac","-movflags","+faststart",str(target)],check=True,capture_output=True);created.append(target);self.log_line(f"Created: {target.name} | score {item.get('score','n/a')} | {item.get('title','')}")
   (outdir/"scores.json").write_text(json.dumps(clips,ensure_ascii=False,indent=2),encoding="utf-8");self.last_output=outdir;self.after(0,lambda:self.open_btn.configure(state="normal"));self.update(f"Finished: {len(created)} clip(s)",1);messagebox.showinfo("ClipForge",f"Finished.\n\nCreated {len(created)} clip(s) in:\n{outdir}")
  except Exception as e:self.update("Error",0);self.log_line("ERROR: "+str(e));messagebox.showerror("ClipForge",str(e))
  finally:
   if wav.exists() and not self.keep_audio.get():
    try:wav.unlink()
    except OSError:pass

def transcribe_windows(wf,models,selected,rate,total,app):
 chunk_seconds=8;overlap_seconds=2;chunk_frames=chunk_seconds*rate;overlap_frames=overlap_seconds*rate;all_words=[];start_frame=0
 while start_frame<total:
  if app.cancel_event.is_set():return []
  wf.setpos(min(start_frame,total));frames=min(chunk_frames,total-start_frame);data=wf.readframes(frames);recognizers={lang:KaldiRecognizer(models[lang],rate) for lang in selected}
  for rec in recognizers.values():rec.SetWords(True);rec.AcceptWaveform(data)
  outputs={lang:json.loads(rec.FinalResult()) for lang,rec in recognizers.items()};chosen=choose_window(outputs,selected)
  for word in chosen:
   word["start"]+=start_frame/rate;word["end"]+=start_frame/rate;all_words.append(word)
  pct=min(1,(start_frame+frames)/total);app.update(f"Transcribing mixed language: {pct*100:.0f}%",.05+.45*pct);start_frame+=max(1,chunk_frames-overlap_frames)
 return merge_words(all_words)

def choose_window(outputs,selected):
 best=[];best_score=-1
 for lang in selected:
  words=outputs[lang].get("result",[]);text=" ".join(w.get("word","") for w in words);score=window_score(text,words,lang)
  if score>best_score:best,best_score=words,score
 return best

def window_score(text,words,lang):
 if not words:return -999
 avg=sum(float(w.get("conf",0)) for w in words)/len(words);letters=re.sub(r"[^A-Za-zΑ-Ωα-ωΆ-Ώά-ώ]","",text);greek=sum(1 for c in letters if "Α"<=c.upper()<="Ώ");latin=sum(1 for c in letters if c.isascii() and c.isalpha());ratio=(greek/(greek+latin)) if greek+latin else 0
 language_bonus=(ratio*0.35 if lang=="Greek" else (1-ratio)*0.35)
 return len(words)*0.03+avg+language_bonus

def merge_words(words):
 result=[]
 for word in sorted(words,key=lambda x:x["start"]):
  if result and word["start"]<result[-1]["end"]-.15:continue
  result.append(word)
 return result

def score_candidates(clips,words,app):
 scored=[]
 for i,candidate in enumerate(clips,1):
  if app.cancel_event.is_set():return []
  text=" ".join(w["word"] for w in words if w["start"]<candidate["end"] and w["end"]>candidate["start"])
  if not text.strip():continue
  app.update(f"AI scoring candidate {i} of {len(clips)}...",.56+.08*i/max(1,len(clips)));app.log_line(f"Scoring candidate {i}: {text[:100]}")
  prompt=("You are a strict short-form video editor. Score this transcript segment for a compelling standalone clip. It may contain Greek, English, or both. Do not invent events. Penalize garbled transcription, incomplete thoughts, greetings, repetition, silence, and segments needing missing context. Reward a clear hook, complete thought, humor, emotion, surprise, conflict, reaction, or memorable phrase. Return only JSON with integer fields score, humor, emotion, surprise, clarity (0-100), plus category, title, reason. Transcript:\n"+text)
  try:
   body={"model":OLLAMA_MODEL,"prompt":prompt,"stream":False,"format":"json","options":{"temperature":0.1}};request=urllib.request.Request(OLLAMA_URL,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
   with urllib.request.urlopen(request,timeout=180) as response:payload=json.loads(response.read().decode());data=json.loads(payload.get("response","{}"))
   item={**candidate,**data};item["score"]=int(item.get("score",0));scored.append(item)
  except Exception as exc:app.log_line(f"AI scoring unavailable: {exc}");scored.append({**candidate,"score":0,"title":"Unscored candidate","reason":"Ollama did not return a valid score."})
 scored.sort(key=lambda item:item.get("score",0),reverse=True);return scored

def make_candidates(words,minlen,maxlen,padding_before,padding_after):
 if not words:return []
 groups=[];start=words[0]["start"];last=words[0]["end"]
 for word in words[1:]:
  if word["start"]-last>1.8 or word["end"]-start>maxlen:groups.append((max(0,start-padding_before),last+padding_after));start=word["start"]
  last=word["end"]
 groups.append((max(0,start-padding_before),last+padding_after));return [{"start":a,"end":min(a+maxlen,b)} for a,b in groups if b-a>=minlen]

def write_srt(words,path):
 lines=[]
 for index,word in enumerate(words,1):
  start=int(word["start"]*1000);end=int(word["end"]*1000);fmt=lambda x:f"{x//3600000:02}:{x%3600000//60000:02}:{x%60000//1000:02},{x%1000:03}";lines += [str(index),f"{fmt(start)} --> {fmt(end)}",word["word"],""]
 path.write_text("\n".join(lines),encoding="utf-8")

if __name__=="__main__":ctk.set_appearance_mode("System");ClipForge().mainloop()
