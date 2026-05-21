import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import { createClient } from "@supabase/supabase-js";
import {
  AreaChart, Area, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

const API          = "http://localhost:8000";
const SUPABASE_URL = "https://xepdxusghwuzepyekbxk.supabase.co";
const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhlcGR4dXNnaHd1emVweWVrYnhrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc3MjQ2OTgsImV4cCI6MjA5MzMwMDY5OH0.zhtZLs9P2BWnbrIjighJTJoZPAxgyV_pLEz2aKAL_dU";
const sb           = createClient(SUPABASE_URL, SUPABASE_KEY);

const S = {
  app      : { minHeight:"100vh", background:"#030712", color:"#e2e8f0", fontFamily:"'Segoe UI',sans-serif", padding:"20px" },
  header   : { display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:"24px", padding:"16px 24px", background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"12px" },
  title    : { fontSize:"24px", fontWeight:"800", color:"#00ff9d", margin:0 },
  subtitle : { fontSize:"12px", color:"#475569", margin:"2px 0 0 0" },
  grid     : { display:"grid", gridTemplateColumns:"repeat(auto-fit, minmax(280px, 1fr))", gap:"16px", marginBottom:"16px" },
  grid2    : { display:"grid", gridTemplateColumns:"1fr 1fr", gap:"16px", marginBottom:"16px" },
  card     : { background:"rgba(255,255,255,0.03)", border:"1px solid rgba(255,255,255,0.08)", borderRadius:"12px", padding:"20px" },
  cardTitle: { fontSize:"11px", fontWeight:"600", color:"#475569", textTransform:"uppercase", letterSpacing:"1px", marginBottom:"16px" },
  statNum  : { fontSize:"40px", fontWeight:"900", lineHeight:"1", margin:"0 0 4px 0" },
  badge    : { display:"inline-block", padding:"3px 10px", borderRadius:"20px", fontSize:"11px", fontWeight:"600" },
  btn      : { padding:"8px 18px", borderRadius:"8px", border:"none", cursor:"pointer", fontWeight:"600", fontSize:"13px" },
  input    : { width:"100%", padding:"10px 12px", background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"8px", color:"#e2e8f0", fontSize:"13px", marginBottom:"10px", outline:"none", boxSizing:"border-box" },
  textarea : { width:"100%", padding:"10px 12px", background:"rgba(255,255,255,0.05)", border:"1px solid rgba(255,255,255,0.1)", borderRadius:"8px", color:"#e2e8f0", fontSize:"13px", marginBottom:"10px", outline:"none", resize:"vertical", minHeight:"80px", boxSizing:"border-box", fontFamily:"inherit" },
  table    : { width:"100%", borderCollapse:"collapse", fontSize:"12px" },
  th       : { padding:"8px 12px", textAlign:"left", color:"#475569", borderBottom:"1px solid rgba(255,255,255,0.06)", fontWeight:"600", fontSize:"10px", textTransform:"uppercase" },
  td       : { padding:"10px 12px", borderBottom:"1px solid rgba(255,255,255,0.04)", color:"#cbd5e1" },
};

const scoreColor = s => s>=75?"#00ff9d":s>=50?"#fbbf24":"#f87171";
const classColor = c => c==="GOOD"?"#00ff9d":c==="WARNING"?"#fbbf24":"#f87171";
const painColor  = p => p<=3?"#00ff9d":p<=6?"#fbbf24":"#f87171";

// ── Token helpers ─────────────────────────────────────────────────────────────
const getToken = async () => {
  try {
    const { data } = await sb.auth.getSession();
    if (data?.session?.access_token) {
      localStorage.setItem("token", data.session.access_token);
      return data.session.access_token;
    }
  } catch {}
  return localStorage.getItem("token") || "";
};

const apiCall = async (method, url, body = null) => {
  let token = await getToken();
  const hdrs = () => ({ headers: { Authorization: `Bearer ${token}` } });
  const exec = async () => {
    if (method==="get")    return await axios.get(url, hdrs());
    if (method==="post")   return await axios.post(url, body, hdrs());
    if (method==="put")    return await axios.put(url, body, hdrs());
    if (method==="delete") return await axios.delete(url, hdrs());
  };
  try {
    return await exec();
  } catch(e) {
    if (e.response?.status === 401) {
      try {
        const { data } = await sb.auth.refreshSession();
        token = data?.session?.access_token || token;
        localStorage.setItem("token", token);
        return await exec();
      } catch {}
    }
    throw e;
  }
};

const CustomTip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background:"#0f172a", border:"1px solid rgba(0,255,157,0.2)", borderRadius:"8px", padding:"10px 14px", fontSize:"12px" }}>
      <div style={{ color:"#64748b", marginBottom:"4px" }}>{label}</div>
      {payload.map((p,i)=><div key={i} style={{ color:p.color||"#00ff9d" }}>{p.name}: {typeof p.value==="number"?p.value.toFixed(1):p.value}</div>)}
    </div>
  );
};

function RingScore({ score, size=120 }) {
  const R=size/2-8, C=2*Math.PI*R, clr=scoreColor(score);
  return (
    <div style={{ position:"relative", width:size, height:size, margin:"0 auto" }}>
      <svg width={size} height={size} style={{ transform:"rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10}/>
        <circle cx={size/2} cy={size/2} r={R} fill="none" stroke={clr} strokeWidth={10}
          strokeDasharray={C} strokeDashoffset={C-(score/100)*C} strokeLinecap="round"
          style={{ filter:`drop-shadow(0 0 6px ${clr})`, transition:"stroke-dashoffset 1s ease" }}/>
      </svg>
      <div style={{ position:"absolute", top:"50%", left:"50%", transform:"translate(-50%,-50%)", textAlign:"center" }}>
        <div style={{ fontSize:"26px", fontWeight:"900", color:clr }}>{score}</div>
        <div style={{ fontSize:"10px", color:"#475569" }}>/ 100</div>
      </div>
    </div>
  );
}

function VoiceCamera({ camState }) {
  const lastMsg=useRef(""), lastFlash=useRef(false), audioCtx=useRef(null);
  const speak=useCallback(t=>{
    if(!t||t===lastMsg.current) return; lastMsg.current=t;
    window.speechSynthesis.cancel();
    const u=new SpeechSynthesisUtterance(t); u.rate=1.1; window.speechSynthesis.speak(u);
  },[]);
  const beep=useCallback(()=>{
    try {
      if(!audioCtx.current) audioCtx.current=new (window.AudioContext||window.webkitAudioContext)();
      const ctx=audioCtx.current, o=ctx.createOscillator(), g=ctx.createGain();
      o.frequency.setValueAtTime(880,ctx.currentTime); o.frequency.exponentialRampToValueAtTime(440,ctx.currentTime+0.12);
      g.gain.setValueAtTime(0.4,ctx.currentTime); g.gain.exponentialRampToValueAtTime(0.001,ctx.currentTime+0.15);
      o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime+0.15);
    }catch{}
  },[]);
  useEffect(()=>{
    if(!camState) return;
    if(camState.voice_message) speak(camState.voice_message);
    if(camState.capture_flash&&!lastFlash.current) beep();
    lastFlash.current=camState.capture_flash;
  },[camState?.voice_message,camState?.capture_flash]);
  return null;
}

function ExerciseTimer({ exercise, onDone }) {
  const [phase,setPhase]=useState("ready"),[count,setCount]=useState(3);
  const [set,setSet]=useState(1),[rep,setRep]=useState(1),[holdT,setHoldT]=useState(0);
  const ref=useRef(null);
  const speak=t=>{const u=new SpeechSynthesisUtterance(t);u.rate=1.1;window.speechSynthesis.speak(u);};
  useEffect(()=>{
    speak(`Starting ${exercise.name||exercise.exercise}. Get ready.`);
    ref.current=setInterval(()=>setCount(c=>{if(c<=1){clearInterval(ref.current);setPhase("exercise");speak("Go!");return 0;}speak(String(c-1));return c-1;}),1000);
    return()=>clearInterval(ref.current);
  },[]);
  useEffect(()=>{
    if(phase!=="exercise") return;
    const hs=exercise.hold_secs||5; speak(`Set ${set} rep ${rep}. Hold ${hs} seconds.`); setHoldT(hs);
    ref.current=setInterval(()=>setHoldT(t=>{
      if(t<=1){clearInterval(ref.current);
        if(rep<(exercise.reps||10)){setRep(r=>r+1);speak("Next rep.");}
        else if(set<(exercise.sets||3)){setSet(s=>s+1);setRep(1);speak("Rest. Next set.");}
        else{setPhase("done");speak("Exercise complete!");}
        return 0;} return t-1;}),1000);
    return()=>clearInterval(ref.current);
  },[phase,set,rep]);
  const hs=exercise.hold_secs||5, pct=holdT/hs;
  return (
    <div style={{ position:"fixed",top:0,left:0,right:0,bottom:0,background:"rgba(0,0,0,0.92)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:1000 }}>
      <div style={{ textAlign:"center",maxWidth:"400px",padding:"40px" }}>
        <div style={{ fontSize:"26px",fontWeight:"800",color:"#00ff9d",marginBottom:"8px" }}>{exercise.name||exercise.exercise}</div>
        <div style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"20px" }}>{exercise.description}</div>
        {phase==="ready"&&<><div style={{ fontSize:"80px",fontWeight:"900",color:"#fbbf24" }}>{count}</div><div style={{ color:"#475569" }}>Get ready...</div></>}
        {phase==="exercise"&&(
          <>
            <div style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"12px" }}>Set {set}/{exercise.sets||3} — Rep {rep}/{exercise.reps||10}</div>
            <div style={{ position:"relative",width:150,height:150,margin:"0 auto 16px" }}>
              <svg width={150} height={150} style={{ transform:"rotate(-90deg)" }}>
                <circle cx={75} cy={75} r={65} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10}/>
                <circle cx={75} cy={75} r={65} fill="none" stroke="#00ff9d" strokeWidth={10}
                  strokeDasharray={2*Math.PI*65} strokeDashoffset={2*Math.PI*65*(1-pct)} strokeLinecap="round"
                  style={{ transition:"stroke-dashoffset 1s linear",filter:"drop-shadow(0 0 8px #00ff9d)" }}/>
              </svg>
              <div style={{ position:"absolute",top:"50%",left:"50%",transform:"translate(-50%,-50%)",textAlign:"center" }}>
                <div style={{ fontSize:"38px",fontWeight:"900",color:"#00ff9d" }}>{holdT}</div>
                <div style={{ fontSize:"10px",color:"#475569" }}>sec</div>
              </div>
            </div>
            <div style={{ color:"#00ff9d",fontSize:"15px",fontWeight:"700" }}>HOLD!</div>
          </>
        )}
        {phase==="done"&&<><div style={{ fontSize:"56px",marginBottom:"12px" }}>🎉</div><div style={{ fontSize:"20px",color:"#00ff9d",fontWeight:"700" }}>Complete!</div></>}
        <button onClick={onDone} style={{ ...S.btn,marginTop:"20px",background:"rgba(255,255,255,0.08)",color:"#94a3b8",border:"1px solid rgba(255,255,255,0.1)" }}>{phase==="done"?"Close":"Skip"}</button>
      </div>
    </div>
  );
}

function LoginPage({ onLogin }) {
  const [mode,setMode]=useState("login");
  const [email,setEmail]=useState(""),[pass,setPass]=useState("");
  const [name,setName]=useState(""),[role,setRole]=useState("user");
  const [age,setAge]=useState(""),[weight,setWeight]=useState(""),[height,setHeight]=useState("");
  const [spec,setSpec]=useState(""),[exp,setExp]=useState(""),[license,setLicense]=useState("");
  const [err,setErr]=useState(""),[loading,setLoading]=useState(false);

  const submit=async()=>{
    setErr(""); setLoading(true);
    try {
      if(mode==="register"){
        const p={email,password:pass,name,role};
        if(role==="user"){ if(age) p.age=+age; if(weight) p.body_weight=+weight; if(height) p.height=+height; }
        else { p.speciality=spec; p.experience=exp; p.license_number=license; }
        const r=await axios.post(`${API}/auth/register`,p);
        if(r.data.success){setErr("✅ Registered! Please login.");setMode("login");}
      } else {
        const r=await axios.post(`${API}/auth/login`,{email,password:pass});
        if(r.data.success){
          await sb.auth.signInWithPassword({email,password:pass});
          localStorage.setItem("token",r.data.access_token);
          localStorage.setItem("user_id",r.data.user_id);
          localStorage.setItem("email",r.data.email);
          localStorage.setItem("name",r.data.name||"");
          localStorage.setItem("role",r.data.role||"user");
          onLogin(r.data);
        }
      }
    }catch(e){setErr(e.response?.data?.detail||"Error. Check credentials.");}
    setLoading(false);
  };

  return (
    <div style={{ minHeight:"100vh",background:"#030712",display:"flex",alignItems:"center",justifyContent:"center" }}>
      <div style={{ width:"100%",maxWidth:"480px",padding:"40px",background:"rgba(255,255,255,0.03)",border:"1px solid rgba(255,255,255,0.08)",borderRadius:"16px",maxHeight:"95vh",overflowY:"auto" }}>
        <div style={{ textAlign:"center",marginBottom:"28px" }}>
          <h1 style={{ fontSize:"30px",fontWeight:"900",color:"#00ff9d",margin:0 }}>PostureAI</h1>
          <p style={{ color:"#475569",fontSize:"13px",marginTop:"4px" }}>AI-Powered Posture Analysis & Physiotherapy</p>
        </div>
        <div style={{ display:"flex",background:"rgba(255,255,255,0.04)",borderRadius:"8px",padding:"4px",marginBottom:"18px" }}>
          {["login","register"].map(m=>(
            <button key={m} onClick={()=>setMode(m)} style={{ flex:1,padding:"8px",border:"none",borderRadius:"6px",cursor:"pointer",fontWeight:"600",fontSize:"13px",background:mode===m?"rgba(0,255,157,0.15)":"transparent",color:mode===m?"#00ff9d":"#475569" }}>
              {m==="login"?"Login":"Register"}
            </button>
          ))}
        </div>
        {mode==="register"&&(
          <>
            <div style={{ display:"flex",gap:"8px",marginBottom:"14px" }}>
              {["user","physiotherapist"].map(r=>(
                <button key={r} onClick={()=>setRole(r)} style={{ flex:1,padding:"11px",border:`1px solid ${role===r?"rgba(0,255,157,0.4)":"rgba(255,255,255,0.08)"}`,borderRadius:"8px",cursor:"pointer",fontWeight:"600",fontSize:"12px",background:role===r?"rgba(0,255,157,0.1)":"rgba(255,255,255,0.03)",color:role===r?"#00ff9d":"#475569" }}>
                  {r==="user"?"👤 Patient":"🏥 Physiotherapist"}
                </button>
              ))}
            </div>
            <input style={S.input} placeholder="Full Name *" value={name} onChange={e=>setName(e.target.value)}/>
            <input style={S.input} placeholder="Email *" type="email" value={email} onChange={e=>setEmail(e.target.value)}/>
            <input style={S.input} placeholder="Password *" type="password" value={pass} onChange={e=>setPass(e.target.value)}/>
            {role==="user"&&(
              <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:"8px" }}>
                <input style={S.input} placeholder="Age" type="number" value={age} onChange={e=>setAge(e.target.value)}/>
                <input style={S.input} placeholder="Weight kg" type="number" value={weight} onChange={e=>setWeight(e.target.value)}/>
                <input style={S.input} placeholder="Height cm" type="number" value={height} onChange={e=>setHeight(e.target.value)}/>
              </div>
            )}
            {role==="physiotherapist"&&(
              <>
                <input style={S.input} placeholder="Speciality" value={spec} onChange={e=>setSpec(e.target.value)}/>
                <input style={S.input} placeholder="Years of Experience" type="number" value={exp} onChange={e=>setExp(e.target.value)}/>
                <input style={S.input} placeholder="License Number *" value={license} onChange={e=>setLicense(e.target.value)}/>
              </>
            )}
          </>
        )}
        {mode==="login"&&(
          <>
            <input style={S.input} placeholder="Email" type="email" value={email} onChange={e=>setEmail(e.target.value)}/>
            <input style={S.input} placeholder="Password" type="password" value={pass} onChange={e=>setPass(e.target.value)} onKeyDown={e=>e.key==="Enter"&&submit()}/>
          </>
        )}
        {err&&<div style={{ padding:"10px 14px",marginBottom:"12px",borderRadius:"8px",fontSize:"13px",background:err.includes("✅")?"rgba(0,255,157,0.08)":"rgba(248,113,113,0.1)",border:`1px solid ${err.includes("✅")?"rgba(0,255,157,0.3)":"rgba(248,113,113,0.3)"}`,color:err.includes("✅")?"#00ff9d":"#f87171" }}>{err}</div>}
        <button onClick={submit} disabled={loading} style={{ ...S.btn,width:"100%",padding:"13px",fontSize:"15px",background:"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)" }}>
          {loading?"Please wait...":mode==="login"?"Login":"Create Account"}
        </button>
      </div>
    </div>
  );
}

function AICard({ ex, onStart }) {
  return (
    <div style={S.card}>
      <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"8px" }}>
        <div style={{ fontSize:"14px",fontWeight:"700" }}>{ex.name||ex.exercise}</div>
        <span style={{ ...S.badge,background:"rgba(167,139,250,0.15)",color:"#a78bfa",fontSize:"10px" }}>AI</span>
      </div>
      {ex.issue&&<div style={{ fontSize:"11px",color:"#475569",marginBottom:"6px" }}>Issue: {ex.issue}</div>}
      <p style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"8px",lineHeight:"1.5" }}>{ex.description}</p>
      {ex.benefit&&<p style={{ fontSize:"12px",color:"#64748b",marginBottom:"8px",fontStyle:"italic" }}>{ex.benefit}</p>}
      <div style={{ display:"flex",gap:"6px",marginBottom:"10px" }}>
        {[{l:"Sets",v:ex.sets||3},{l:"Reps",v:ex.reps||10},{l:"Hold",v:`${ex.hold_secs||5}s`},{l:"Freq",v:ex.frequency||"Daily"}].map(item=>(
          <div key={item.l} style={{ flex:1,background:"rgba(255,255,255,0.04)",borderRadius:"6px",padding:"6px",textAlign:"center" }}>
            <div style={{ fontSize:"12px",fontWeight:"700",color:"#a78bfa" }}>{item.v}</div>
            <div style={{ fontSize:"9px",color:"#475569" }}>{item.l}</div>
          </div>
        ))}
      </div>
      <button onClick={()=>onStart(ex)} style={{ ...S.btn,width:"100%",background:"rgba(167,139,250,0.1)",color:"#a78bfa",border:"1px solid rgba(167,139,250,0.3)",fontSize:"12px" }}>Start Timer</button>
    </div>
  );
}

function BigImage({ src, label, fallbackSrc }) {
  const [open,setOpen]=useState(false);
  const [imgSrc,setImgSrc]=useState(src);
  const [tries,setTries]=useState(0);
  useEffect(()=>{setImgSrc(src);setTries(0);},[src]);
  const onErr=()=>{
    setTries(t=>{
      const n=t+1;
      if(n===1&&fallbackSrc) setImgSrc(fallbackSrc);
      else if(n===2){ const nm=src.split('/').pop().split('\\').pop(); setImgSrc(`${API}/snapshots/view/${nm}`); }
      return n;
    });
  };
  return (
    <>
      {open&&(
        <div onClick={()=>setOpen(false)} style={{ position:"fixed",top:0,left:0,right:0,bottom:0,background:"rgba(0,0,0,0.96)",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",zIndex:2000,cursor:"zoom-out" }}>
          <img src={imgSrc} alt={label} onError={onErr} style={{ maxWidth:"95vw",maxHeight:"88vh",borderRadius:"8px",objectFit:"contain",border:"1px solid rgba(255,255,255,0.1)" }}/>
          {label&&<div style={{ color:"#94a3b8",fontSize:"13px",marginTop:"10px" }}>{label}</div>}
          <div style={{ color:"#475569",fontSize:"11px",marginTop:"4px" }}>Click to close</div>
        </div>
      )}
      <div style={{ position:"relative",cursor:"zoom-in" }} onClick={()=>setOpen(true)}>
        <img src={imgSrc} alt={label} onError={onErr} style={{ width:"100%",borderRadius:"6px",marginBottom:"6px",objectFit:"cover",height:"130px",display:"block",background:"rgba(255,255,255,0.05)" }}/>
        <div style={{ position:"absolute",top:"5px",right:"5px",background:"rgba(0,0,0,0.6)",borderRadius:"4px",padding:"2px 5px",fontSize:"10px",color:"white" }}>🔍</div>
      </div>
    </>
  );
}

function SnapshotManager({ snapshots, onDelete, onAnalyze, onRefresh }) {
  const [analyzing,setAnalyzing]=useState(null);
  const getUrl=s=>{ if(s.url&&s.url.startsWith("http")&&!s.url.includes("localhost")) return s.url; if(s.storage_url&&s.storage_url.startsWith("http")) return s.storage_url; return `${API}/snapshots/view/${s.filename||s.name}`; };
  const analyze=async s=>{ const n=s.filename||s.name; setAnalyzing(n); try{ const r=await axios.post(`${API}/posture/analyze-snapshot`,{filename:n}); if(onAnalyze) onAnalyze(r.data); }catch{alert("Analysis failed");} setAnalyzing(null); };
  if(!snapshots.length) return <div style={S.card}><p style={{ color:"#475569" }}>No snapshots yet. Use Live Camera to capture.</p></div>;
  return (
    <div>
      <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"16px" }}>
        <div style={S.cardTitle}>Snapshots ({snapshots.length})</div>
        <button onClick={onRefresh} style={{ ...S.btn,background:"rgba(255,255,255,0.05)",color:"#64748b",border:"1px solid rgba(255,255,255,0.08)",fontSize:"12px" }}>Refresh</button>
      </div>
      <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:"12px" }}>
        {snapshots.map((snap,i)=>{
          const n=snap.filename||snap.name||`snap_${i}`;
          const label=n.replace("snapshot_","").replace(".jpg","").replace(/_/g," ");
          const url=getUrl(snap);
          return (
            <div key={i} style={{ ...S.card,padding:"12px" }}>
              <BigImage src={url} fallbackSrc={`${API}/snapshots/view/${n}`} label={label}/>
              <div style={{ fontSize:"10px",color:"#475569",marginBottom:"8px" }}>{label}</div>
              <div style={{ display:"flex",gap:"6px" }}>
                <button onClick={()=>analyze(snap)} disabled={analyzing===n} style={{ ...S.btn,flex:1,background:"rgba(167,139,250,0.1)",color:"#a78bfa",border:"1px solid rgba(167,139,250,0.3)",fontSize:"11px",padding:"6px" }}>{analyzing===n?"...":"AI Analyze"}</button>
                {onDelete&&<button onClick={()=>onDelete(n)} style={{ ...S.btn,background:"rgba(248,113,113,0.1)",color:"#f87171",border:"1px solid rgba(248,113,113,0.3)",fontSize:"11px",padding:"6px 10px" }}>Del</button>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function NearbyDoctors() {
  const [pos,setPos]=useState(null),[docs,setDocs]=useState([]),[loading,setLoading]=useState(false),[err,setErr]=useState(""),[filter,setFilter]=useState("all");
  const mapDiv=useRef(null),mapObj=useRef(null);
  const loadLeaflet=()=>new Promise(resolve=>{ if(window.L){resolve();return;} if(!document.getElementById("lf-css")){const css=document.createElement("link");css.id="lf-css";css.rel="stylesheet";css.href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";document.head.appendChild(css);} if(!document.getElementById("lf-js")){const s=document.createElement("script");s.id="lf-js";s.src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";s.onload=()=>setTimeout(resolve,100);document.head.appendChild(s);}else setTimeout(resolve,100); });
  const locate=async()=>{ setLoading(true);setErr(""); await loadLeaflet(); if(!navigator.geolocation){setErr("Geolocation not supported");setLoading(false);return;} navigator.geolocation.getCurrentPosition(async p=>{ const lp={lat:p.coords.latitude,lng:p.coords.longitude}; setPos(lp); await fetchDocs(lp.lat,lp.lng); },()=>{setErr("Location denied.");setLoading(false);}); };
  const fetchDocs=async(lat,lng)=>{ try{ const q=`[out:json][timeout:25];(node["healthcare"="physiotherapist"](around:5000,${lat},${lng});node["healthcare"="doctor"](around:5000,${lat},${lng});node["amenity"="doctors"](around:5000,${lat},${lng});node["amenity"="clinic"](around:5000,${lat},${lng});node["amenity"="hospital"](around:5000,${lat},${lng}););out body;`; const res=await fetch("https://overpass-api.de/api/interpreter",{method:"POST",body:`data=${encodeURIComponent(q)}`,headers:{"Content-Type":"application/x-www-form-urlencoded"}}); const data=await res.json(); const places=(data.elements||[]).filter(e=>e.lat&&e.lon).map(e=>({id:e.id,name:e.tags?.name||"Medical Center",lat:e.lat,lng:e.lon,type:e.tags?.healthcare||e.tags?.amenity||"clinic",phone:e.tags?.phone||"",address:[e.tags?.["addr:housenumber"],e.tags?.["addr:street"],e.tags?.["addr:city"]].filter(Boolean).join(", "),opening:e.tags?.opening_hours||""})).slice(0,40); setDocs(places); }catch{setErr("Could not load nearby places.");} setLoading(false); };
  const navigate=d=>{ if(!pos) return; window.open(`https://www.google.com/maps/dir/?api=1&origin=${pos.lat},${pos.lng}&destination=${d.lat},${d.lng}&travelmode=driving`,"_blank"); };
  useEffect(()=>{
    if(!pos||!mapDiv.current||!window.L) return;
    const L=window.L;
    if(mapObj.current){mapObj.current.remove();mapObj.current=null;}
    const map=L.map(mapDiv.current,{center:[pos.lat,pos.lng],zoom:14}); mapObj.current=map;
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{attribution:"© OpenStreetMap"}).addTo(map);
    L.circleMarker([pos.lat,pos.lng],{radius:10,color:"#a78bfa",fillColor:"#a78bfa",fillOpacity:1}).addTo(map).bindPopup("<b>📍 You</b>").openPopup();
    const filtered=filter==="all"?docs:docs.filter(d=>filter==="physio"?(d.type==="physiotherapist"||d.name.toLowerCase().includes("physio")):d.type==="hospital");
    filtered.forEach(d=>{ const color=d.type==="hospital"?"#f87171":d.type==="physiotherapist"?"#00ff9d":"#38bdf8"; const gUrl=`https://www.google.com/maps/dir/?api=1&origin=${pos.lat},${pos.lng}&destination=${d.lat},${d.lng}&travelmode=driving`; const popup=`<div style="font-family:sans-serif;min-width:190px"><b>${d.name}</b><br/><span style="font-size:11px;color:#888;text-transform:capitalize">${d.type.replace("_"," ")}</span>${d.address?`<br/>📍 ${d.address}`:""} ${d.phone?`<br/>📞 <a href="tel:${d.phone}">${d.phone}</a>`:""} ${d.opening?`<br/>🕒 ${d.opening}`:""}<br/><a href="${gUrl}" target="_blank" style="display:inline-block;margin-top:6px;background:#4285f4;color:white;padding:4px 10px;border-radius:4px;font-size:11px;text-decoration:none">🗺️ Get Directions</a></div>`; L.circleMarker([d.lat,d.lng],{radius:8,color,fillColor:color,fillOpacity:0.85,weight:2}).addTo(map).bindPopup(popup); });
    setTimeout(()=>map.invalidateSize(),300);
    return()=>{ if(mapObj.current){mapObj.current.remove();mapObj.current=null;} };
  },[pos,docs,filter]);
  const filtered=filter==="all"?docs:docs.filter(d=>filter==="physio"?(d.type==="physiotherapist"||d.name.toLowerCase().includes("physio")):d.type==="hospital");
  return (
    <div>
      <div style={{ ...S.card,marginBottom:"16px" }}>
        <div style={S.cardTitle}>Find Nearby Physiotherapists & Doctors</div>
        <button onClick={locate} disabled={loading} style={{ ...S.btn,padding:"12px 24px",background:"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)",fontSize:"14px" }}>{loading?"📍 Locating...":"📍 Find Doctors Near Me"}</button>
        {err&&<p style={{ color:"#f87171",fontSize:"13px",marginTop:"8px" }}>{err}</p>}
      </div>
      {pos&&(
        <>
          <div style={{ display:"flex",gap:"8px",marginBottom:"12px",flexWrap:"wrap",alignItems:"center" }}>
            {[{id:"all",l:"All"},{id:"physio",l:"Physiotherapists"},{id:"hospital",l:"Hospitals"}].map(f=>(
              <button key={f.id} onClick={()=>setFilter(f.id)} style={{ ...S.btn,fontSize:"12px",background:filter===f.id?"rgba(0,255,157,0.15)":"rgba(255,255,255,0.04)",color:filter===f.id?"#00ff9d":"#64748b",border:filter===f.id?"1px solid rgba(0,255,157,0.4)":"1px solid rgba(255,255,255,0.06)" }}>{f.l}</button>
            ))}
            <span style={{ fontSize:"12px",color:"#475569" }}>{filtered.length} found</span>
          </div>
          <div style={{ borderRadius:"12px",overflow:"hidden",marginBottom:"16px",border:"1px solid rgba(255,255,255,0.08)" }}>
            <div ref={mapDiv} style={{ width:"100%",height:"420px" }}/>
          </div>
          {filtered.length>0&&(
            <div style={S.grid}>
              {filtered.slice(0,6).map((d,i)=>(
                <div key={i} style={S.card}>
                  <div style={{ fontWeight:"700",fontSize:"14px",marginBottom:"6px" }}>{d.name}</div>
                  <span style={{ ...S.badge,background:"rgba(56,189,248,0.1)",color:"#38bdf8",fontSize:"10px",marginBottom:"8px",display:"inline-block",textTransform:"capitalize" }}>{d.type.replace("_"," ")}</span>
                  {d.address&&<div style={{ fontSize:"12px",color:"#64748b",marginBottom:"4px" }}>📍 {d.address}</div>}
                  {d.phone&&<div style={{ fontSize:"12px",marginBottom:"4px" }}>📞 <a href={`tel:${d.phone}`} style={{ color:"#00ff9d" }}>{d.phone}</a></div>}
                  {d.opening&&<div style={{ fontSize:"11px",color:"#475569",marginBottom:"8px" }}>🕒 {d.opening}</div>}
                  <div style={{ display:"flex",gap:"6px" }}>
                    <button onClick={()=>navigate(d)} style={{ ...S.btn,flex:1,background:"rgba(66,133,244,0.15)",color:"#4285f4",border:"1px solid rgba(66,133,244,0.4)",fontSize:"11px",padding:"7px" }}>🗺️ Directions</button>
                    {d.phone&&<a href={`tel:${d.phone}`} style={{ ...S.btn,textAlign:"center",background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",textDecoration:"none",fontSize:"11px",padding:"7px 10px" }}>📞</a>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Share Report Panel ────────────────────────────────────────────────────────
function ShareReportPanel({ camState, consultations, snapshots }) {
  const [sel,setSel]=useState(""),[sharing,setSharing]=useState(false),[status,setStatus]=useState("");
  const all=consultations.filter(c=>c.status==="active"||c.status==="pending");
  const share=async()=>{
    if(!sel){setStatus("Select a physiotherapist");return;}
    setSharing(true); setStatus("");
    try {
      const c=all.find(x=>x.id===sel);
      await apiCall("post",`${API}/consult/share-report`,{
        consultation_id:sel, physio_id:c?.physio_id,
        features:camState?.features||{}, result:camState?.score||{}, risk:camState?.risk||{},
        snapshot_urls:snapshots.map(s=>s.url||s.storage_url||`${API}/snapshots/view/${s.filename||s.name}`).filter(Boolean),
        snapshot_names:snapshots.map(s=>s.filename||s.name).filter(Boolean),
      });
      setStatus("✅ Report shared with physiotherapist!");
    }catch(e){setStatus("❌ "+(e.response?.data?.detail||"Failed"));}
    setSharing(false);
  };
  return (
    <div style={{ ...S.card,borderColor:"rgba(0,255,157,0.25)",marginTop:"8px" }}>
      <div style={S.cardTitle}>📊 Share Report with Physiotherapist</div>
      {!all.length
        ?<p style={{ color:"#475569",fontSize:"13px" }}>No consultations. Contact a physiotherapist first.</p>
        :(
          <>
            <select value={sel} onChange={e=>setSel(e.target.value)} style={{ ...S.input,cursor:"pointer" }}>
              <option value="">-- Select Physiotherapist --</option>
              {all.map((c,i)=><option key={i} value={c.id}>Dr. {c.profiles?.name||"Physiotherapist"} ({c.status})</option>)}
            </select>
            {camState?.score&&(
              <div style={{ padding:"10px",background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.15)",borderRadius:"8px",marginBottom:"12px" }}>
                <div style={{ display:"flex",gap:"20px" }}>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Score</div><div style={{ fontSize:"20px",fontWeight:"700",color:scoreColor(camState.score.score||0) }}>{camState.score.score||0}/100</div></div>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Risk</div><div style={{ fontSize:"20px",fontWeight:"700",color:"#f87171" }}>{camState.risk?.risk_score||0}/100</div></div>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Class</div><div style={{ fontSize:"15px",fontWeight:"700",color:classColor(camState.score.classification||"") }}>{camState.score.classification||"—"}</div></div>
                </div>
              </div>
            )}
            {snapshots.length>0&&(
              <div style={{ display:"flex",gap:"6px",marginBottom:"12px" }}>
                {snapshots.slice(0,3).map((s,i)=>{ const url=s.url||s.storage_url||`${API}/snapshots/view/${s.filename||s.name}`; return <img key={i} src={url} alt="" onError={e=>{e.target.style.display="none";}} style={{ width:"65px",height:"50px",objectFit:"cover",borderRadius:"4px",border:"1px solid rgba(0,255,157,0.3)" }}/>; })}
              </div>
            )}
            <button onClick={share} disabled={sharing} style={{ ...S.btn,width:"100%",padding:"12px",background:sharing?"rgba(100,100,100,0.15)":"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)",fontSize:"14px",fontWeight:"700" }}>
              {sharing?"Sharing...":"📊 Share Report & Snapshots"}
            </button>
            {status&&<p style={{ marginTop:"8px",fontSize:"13px",color:status.includes("✅")?"#00ff9d":"#f87171",textAlign:"center" }}>{status}</p>}
          </>
        )
      }
    </div>
  );
}

// ── Daily Log Modal ───────────────────────────────────────────────────────────
function DailyLogModal({ camState, consultations, prescriptions, onClose, onLogged }) {
  const [pain,setPain]=useState(5);
  const [notes,setNotes]=useState("");
  const [doneExs,setDoneExs]=useState([]);
  const [saving,setSaving]=useState(false);
  const [sel,setSel]=useState(consultations.filter(c=>c.status==="active")[0]?.id||"");

  // Collect all exercises from prescriptions + AI
  const allExercises=[
    ...prescriptions.flatMap(p=>(p.exercises||[]).map(e=>e.exercise||e.name||e)),
  ].filter(Boolean).filter((v,i,a)=>a.indexOf(v)===i);

  const save=async()=>{
    setSaving(true);
    try {
      await apiCall("post",`${API}/consult/log-daily`,{
        consultation_id: sel||null,
        posture_score  : camState?.score?.score||0,
        risk_score     : camState?.risk?.risk_score||0,
        classification : camState?.score?.classification||"N/A",
        exercises_done : doneExs,
        pain_level     : pain,
        notes,
        features       : camState?.features||{},
      });
      if(onLogged) onLogged();
      onClose();
    }catch(e){alert("Failed to log: "+e.message);}
    setSaving(false);
  };

  return (
    <div style={{ position:"fixed",top:0,left:0,right:0,bottom:0,background:"rgba(0,0,0,0.85)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:1500 }}>
      <div style={{ background:"#0f172a",border:"1px solid rgba(0,255,157,0.2)",borderRadius:"16px",padding:"30px",maxWidth:"500px",width:"90%",maxHeight:"90vh",overflowY:"auto" }}>
        <div style={{ fontSize:"18px",fontWeight:"800",color:"#00ff9d",marginBottom:"20px" }}>📅 Daily Posture Log</div>

        {/* Today's score */}
        {camState?.score&&(
          <div style={{ display:"flex",gap:"16px",marginBottom:"20px",padding:"12px",background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.15)",borderRadius:"8px" }}>
            <div><div style={{ fontSize:"10px",color:"#475569" }}>Today's Score</div><div style={{ fontSize:"24px",fontWeight:"900",color:scoreColor(camState.score.score||0) }}>{camState.score.score||0}/100</div></div>
            <div><div style={{ fontSize:"10px",color:"#475569" }}>Risk</div><div style={{ fontSize:"24px",fontWeight:"900",color:"#f87171" }}>{camState.risk?.risk_score||0}/100</div></div>
            <div><div style={{ fontSize:"10px",color:"#475569" }}>Class</div><div style={{ fontSize:"14px",fontWeight:"700",marginTop:"4px",color:classColor(camState.score.classification||"") }}>{camState.score.classification||"—"}</div></div>
          </div>
        )}

        {/* Pain level */}
        <div style={{ marginBottom:"16px" }}>
          <div style={{ fontSize:"12px",color:"#475569",marginBottom:"8px",textTransform:"uppercase",letterSpacing:"1px" }}>Pain Level: <span style={{ color:painColor(pain),fontWeight:"700" }}>{pain}/10</span></div>
          <input type="range" min="0" max="10" value={pain} onChange={e=>setPain(+e.target.value)} style={{ width:"100%",accentColor:"#00ff9d" }}/>
          <div style={{ display:"flex",justifyContent:"space-between",fontSize:"10px",color:"#475569" }}>
            <span>No Pain</span><span>Moderate</span><span>Severe</span>
          </div>
        </div>

        {/* Exercises done */}
        {allExercises.length>0&&(
          <div style={{ marginBottom:"16px" }}>
            <div style={{ fontSize:"12px",color:"#475569",marginBottom:"8px",textTransform:"uppercase",letterSpacing:"1px" }}>Exercises Completed Today</div>
            {allExercises.map((ex,i)=>(
              <div key={i} onClick={()=>setDoneExs(d=>d.includes(ex)?d.filter(x=>x!==ex):[...d,ex])}
                style={{ padding:"8px 12px",marginBottom:"6px",borderRadius:"6px",cursor:"pointer",fontSize:"13px",
                  background:doneExs.includes(ex)?"rgba(0,255,157,0.1)":"rgba(255,255,255,0.04)",
                  border:`1px solid ${doneExs.includes(ex)?"rgba(0,255,157,0.4)":"rgba(255,255,255,0.08)"}`,
                  color:doneExs.includes(ex)?"#00ff9d":"#94a3b8",
                  display:"flex",alignItems:"center",gap:"8px" }}>
                <span>{doneExs.includes(ex)?"✅":"⬜"}</span> {ex}
              </div>
            ))}
          </div>
        )}

        {/* Link to consultation */}
        {consultations.filter(c=>c.status==="active").length>0&&(
          <div style={{ marginBottom:"16px" }}>
            <div style={{ fontSize:"12px",color:"#475569",marginBottom:"6px",textTransform:"uppercase",letterSpacing:"1px" }}>Link to Consultation</div>
            <select value={sel} onChange={e=>setSel(e.target.value)} style={{ ...S.input,marginBottom:0 }}>
              <option value="">None</option>
              {consultations.filter(c=>c.status==="active").map((c,i)=><option key={i} value={c.id}>Dr. {c.profiles?.name||"Physiotherapist"}</option>)}
            </select>
          </div>
        )}

        <textarea style={S.textarea} placeholder="Notes about today (pain location, improvements, etc.)" value={notes} onChange={e=>setNotes(e.target.value)}/>

        <div style={{ display:"flex",gap:"8px" }}>
          <button onClick={onClose} style={{ ...S.btn,flex:1,background:"rgba(255,255,255,0.05)",color:"#64748b",border:"1px solid rgba(255,255,255,0.08)" }}>Cancel</button>
          <button onClick={save} disabled={saving} style={{ ...S.btn,flex:2,background:"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)",padding:"10px" }}>
            {saving?"Saving...":"📅 Log Today's Progress"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Patient Progress View (for Physio) ────────────────────────────────────────
function PatientProgress({ consultation, physio, onBack }) {
  const [progress,setProgress]=useState(null),[loading,setLoading]=useState(true);
  const [activeTab,setActiveTab]=useState("overview");
  const [presTitle,setPresTitle]=useState("Exercise Prescription");
  const [presExs,setPresExs]=useState(""),[presNotes,setPresNotes]=useState("");
  const [guidance,setGuidance]=useState(""),[notes,setNotes]=useState("");
  const [sending,setSending]=useState(false);

  const patientId=consultation.user_id||consultation.profiles?.id;

  const load=useCallback(async()=>{
    setLoading(true);
    try {
      const r=await apiCall("get",`${API}/consult/patient-progress/${patientId}`);
      setProgress(r.data);
    }catch(e){console.log("Progress error:",e);}
    setLoading(false);
  },[patientId]);

  useEffect(()=>{load();},[load]);

  const createPresc=async()=>{
    setSending(true);
    try {
      const ex=presExs.split("\n").filter(e=>e.trim()).map(e=>({ exercise:e.trim(), sets:3, reps:10, hold_secs:5 }));
      await apiCall("post",`${API}/consult/prescribe`,{ consultation_id:consultation.id, user_id:patientId, title:presTitle, exercises:ex, notes:presNotes });
      load(); alert("Prescription sent to patient!");
      setPresExs(""); setPresNotes(""); setPresTitle("Exercise Prescription");
    }catch(e){alert("Failed: "+e.message);}
    setSending(false);
  };

  const addGuidance=async reportId=>{
    try {
      await apiCall("post",`${API}/consult/add-guidance/${reportId}`,{notes,guidance});
      load(); alert("Guidance added!");
    }catch{}
  };

  if(loading) return <div style={{ ...S.card,textAlign:"center",padding:"40px" }}><div style={{ color:"#00ff9d",fontSize:"16px" }}>Loading patient data...</div></div>;
  if(!progress) return <div style={S.card}><p style={{ color:"#f87171" }}>Failed to load patient data.</p></div>;

  const p       = progress.patient||{};
  const access  = progress.access_granted;
  const tracking= progress.tracking||[];
  const reports = progress.reports||[];
  const prescs  = progress.prescriptions||[];
  const history = progress.full_history||[];

  // Chart data
  const chartData = (access?history:tracking).map(t=>({
    date  : t.date,
    score : t.posture_score||0,
    risk  : t.risk_score||0,
    pain  : (t.pain_level||0)*10, // scale 0-100
  }));

  const avgScore = tracking.length ? Math.round(tracking.reduce((a,t)=>a+(t.posture_score||0),0)/tracking.length) : 0;
  const avgRisk  = tracking.length ? Math.round(tracking.reduce((a,t)=>a+(t.risk_score||0),0)/tracking.length) : 0;
  const trend    = tracking.length>=2 ? (tracking[0].posture_score > tracking[tracking.length-1].posture_score ? "IMPROVING" : "WORSENING") : "STABLE";

  return (
    <div>
      <button onClick={onBack} style={{ ...S.btn,marginBottom:"16px",background:"rgba(255,255,255,0.05)",color:"#94a3b8",border:"1px solid rgba(255,255,255,0.08)" }}>← Back to Patients</button>

      {/* Patient Header */}
      <div style={{ ...S.card,marginBottom:"16px",borderColor:"rgba(56,189,248,0.3)" }}>
        <div style={{ display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:"12px" }}>
          <div>
            <div style={{ fontSize:"20px",fontWeight:"800",marginBottom:"6px" }}>👤 {p.name||"Patient"}</div>
            <div style={{ display:"flex",gap:"16px",flexWrap:"wrap" }}>
              {p.age&&<span style={{ fontSize:"13px",color:"#64748b" }}>Age: {p.age}</span>}
              {p.body_weight&&<span style={{ fontSize:"13px",color:"#64748b" }}>Weight: {p.body_weight}kg</span>}
              {p.height&&<span style={{ fontSize:"13px",color:"#64748b" }}>Height: {p.height}cm</span>}
            </div>
            <div style={{ marginTop:"8px",display:"flex",gap:"8px",flexWrap:"wrap" }}>
              <span style={{ ...S.badge,background:"rgba(0,255,157,0.1)",color:"#00ff9d" }}>{consultation.status}</span>
              {access
                ? <span style={{ ...S.badge,background:"rgba(0,255,157,0.15)",color:"#00ff9d" }}>🔓 Full Access Granted</span>
                : <span style={{ ...S.badge,background:"rgba(251,191,36,0.1)",color:"#fbbf24" }}>🔒 Basic Access</span>
              }
            </div>
          </div>
          <div style={{ display:"flex",gap:"16px" }}>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontSize:"11px",color:"#475569" }}>Avg Score</div>
              <div style={{ fontSize:"24px",fontWeight:"900",color:scoreColor(avgScore) }}>{avgScore}</div>
            </div>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontSize:"11px",color:"#475569" }}>Avg Risk</div>
              <div style={{ fontSize:"24px",fontWeight:"900",color:"#f87171" }}>{avgRisk}</div>
            </div>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontSize:"11px",color:"#475569" }}>Trend</div>
              <div style={{ fontSize:"18px",fontWeight:"900",color:trend==="IMPROVING"?"#00ff9d":trend==="WORSENING"?"#f87171":"#fbbf24" }}>
                {trend==="IMPROVING"?"↑":trend==="WORSENING"?"↓":"→"}
              </div>
            </div>
          </div>
        </div>
        {!access&&<div style={{ marginTop:"12px",padding:"10px 14px",background:"rgba(251,191,36,0.05)",border:"1px solid rgba(251,191,36,0.2)",borderRadius:"8px",fontSize:"12px",color:"#fbbf24" }}>
          ⚠️ Patient hasn't granted full access yet. Ask them to grant access from their consultation page for detailed history.
        </div>}
      </div>

      {/* Sub tabs */}
      <div style={{ display:"flex",gap:"8px",marginBottom:"16px",flexWrap:"wrap" }}>
        {["overview","progress","reports","prescribe"].map(t=>(
          <button key={t} onClick={()=>setActiveTab(t)} style={{ ...S.btn,background:activeTab===t?"rgba(0,255,157,0.15)":"rgba(255,255,255,0.04)",color:activeTab===t?"#00ff9d":"#64748b",border:activeTab===t?"1px solid rgba(0,255,157,0.4)":"1px solid rgba(255,255,255,0.06)",textTransform:"capitalize",fontSize:"12px" }}>{t}</button>
        ))}
      </div>

      {/* Overview */}
      {activeTab==="overview"&&(
        <>
          <div style={S.grid}>
            <div style={S.card}><div style={S.cardTitle}>Days Tracked</div><p style={{ ...S.statNum,color:"#38bdf8" }}>{tracking.length}</p></div>
            <div style={S.card}><div style={S.cardTitle}>Reports Shared</div><p style={{ ...S.statNum,color:"#a78bfa" }}>{reports.length}</p></div>
            <div style={S.card}><div style={S.cardTitle}>Prescriptions</div><p style={{ ...S.statNum,color:"#00ff9d" }}>{prescs.length}</p></div>
          </div>

          {/* Recent tracking */}
          {tracking.length>0&&(
            <div style={S.card}>
              <div style={S.cardTitle}>Recent Daily Logs</div>
              <div style={{ overflowX:"auto" }}>
                <table style={S.table}>
                  <thead><tr>{["Date","Score","Risk","Pain","Exercises Done","Notes"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
                  <tbody>{tracking.slice(0,7).map((t,i)=>(
                    <tr key={i} style={{ background:i%2===0?"rgba(255,255,255,0.01)":"transparent" }}>
                      <td style={S.td}>{t.date}</td>
                      <td style={{ ...S.td,color:scoreColor(t.posture_score||0),fontWeight:"700" }}>{t.posture_score?.toFixed(0)||"—"}/100</td>
                      <td style={{ ...S.td,color:"#f87171",fontWeight:"700" }}>{t.risk_score?.toFixed(0)||"—"}/100</td>
                      <td style={{ ...S.td,color:painColor(t.pain_level||0) }}>{t.pain_level||0}/10</td>
                      <td style={S.td}>{(t.exercises_done||[]).length} done</td>
                      <td style={{ ...S.td,maxWidth:"150px",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap" }}>{t.notes||"—"}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* Progress Charts */}
      {activeTab==="progress"&&(
        <>
          {!access&&tracking.length===0&&(
            <div style={{ ...S.card,textAlign:"center",padding:"24px" }}>
              <div style={{ fontSize:"32px",marginBottom:"12px" }}>📊</div>
              <p style={{ color:"#475569" }}>No tracking data yet. Patient needs to log daily progress.</p>
            </div>
          )}
          {chartData.length>0&&(
            <>
              <div style={S.card}>
                <div style={S.cardTitle}>Posture Score Progress {access?"(Full History)":"(Recent)"}</div>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)"/>
                    <XAxis dataKey="date" tick={{ fill:"#475569",fontSize:9 }} axisLine={false}/>
                    <YAxis domain={[0,100]} tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                    <Tooltip content={<CustomTip/>}/>
                    <Legend wrapperStyle={{ fontSize:"12px",color:"#94a3b8" }}/>
                    <Line type="monotone" dataKey="score" name="Posture Score" stroke="#00ff9d" strokeWidth={2} dot={{ r:3,fill:"#00ff9d" }}/>
                    <Line type="monotone" dataKey="risk" name="Risk Score" stroke="#f87171" strokeWidth={2} dot={{ r:3,fill:"#f87171" }}/>
                    <Line type="monotone" dataKey="pain" name="Pain×10" stroke="#fbbf24" strokeWidth={1} dot={false} strokeDasharray="4 4"/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
              {/* Exercises adherence */}
              <div style={S.card}>
                <div style={S.cardTitle}>Exercise Adherence</div>
                <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(120px,1fr))",gap:"8px" }}>
                  {(access?history:tracking).slice(0,14).map((t,i)=>(
                    <div key={i} style={{ padding:"8px",background:"rgba(255,255,255,0.03)",borderRadius:"6px",border:"1px solid rgba(255,255,255,0.06)",textAlign:"center" }}>
                      <div style={{ fontSize:"10px",color:"#475569",marginBottom:"4px" }}>{t.date}</div>
                      <div style={{ fontSize:"14px",fontWeight:"700",color:(t.exercises_done||[]).length>0?"#00ff9d":"#f87171" }}>
                        {(t.exercises_done||[]).length>0?"✓":"✗"}
                      </div>
                      <div style={{ fontSize:"10px",color:"#64748b" }}>{(t.exercises_done||[]).length} done</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* Reports */}
      {activeTab==="reports"&&(
        <div>
          {reports.length===0
            ?<div style={S.card}><p style={{ color:"#475569" }}>No reports shared yet.</p></div>
            :reports.map((r,i)=>(
              <div key={i} style={{ ...S.card,marginBottom:"12px",borderColor:r.status==="reviewed"?"rgba(0,255,157,0.2)":"rgba(255,255,255,0.08)" }}>
                <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"12px" }}>
                  <div style={{ fontWeight:"700" }}>Report #{i+1} — {new Date(r.created_at).toLocaleDateString()}</div>
                  <span style={{ ...S.badge,background:r.status==="reviewed"?"rgba(0,255,157,0.1)":"rgba(251,191,36,0.1)",color:r.status==="reviewed"?"#00ff9d":"#fbbf24" }}>{r.status}</span>
                </div>
                <div style={{ display:"flex",gap:"20px",marginBottom:"12px" }}>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Score</div><div style={{ fontSize:"22px",fontWeight:"900",color:scoreColor(r.posture_score||0) }}>{r.posture_score?.toFixed(0)||0}/100</div></div>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Risk</div><div style={{ fontSize:"22px",fontWeight:"900",color:"#f87171" }}>{r.risk_score?.toFixed(0)||0}/100</div></div>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Class</div><span style={{ ...S.badge,background:`${classColor(r.classification)}22`,color:classColor(r.classification),marginTop:"4px",display:"inline-block" }}>{r.classification||"N/A"}</span></div>
                </div>
                {r.features&&(
                  <div style={{ marginBottom:"12px" }}>
                    {Object.entries(r.features).map(([k,v])=>v!=null&&(
                      <div key={k} style={{ display:"flex",justifyContent:"space-between",fontSize:"12px",padding:"3px 0",borderBottom:"1px solid rgba(255,255,255,0.04)" }}>
                        <span style={{ color:"#64748b" }}>{k.replace(/_/g," ").replace(/\b\w/g,l=>l.toUpperCase())}</span>
                        <span style={{ color:"#e2e8f0",fontWeight:"600" }}>{parseFloat(v).toFixed(1)}</span>
                      </div>
                    ))}
                  </div>
                )}
                {r.physio_guidance&&(
                  <div style={{ padding:"10px",background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.15)",borderRadius:"8px" }}>
                    <div style={{ fontSize:"11px",color:"#00ff9d",marginBottom:"4px",textTransform:"uppercase" }}>Your Guidance</div>
                    <p style={{ fontSize:"13px",color:"#94a3b8",margin:0 }}>{r.physio_guidance}</p>
                  </div>
                )}
                {r.status==="pending"&&(
                  <div style={{ marginTop:"12px" }}>
                    <div style={{ fontSize:"11px",color:"#475569",marginBottom:"8px",textTransform:"uppercase" }}>Add Your Guidance</div>
                    <textarea style={S.textarea} placeholder="Clinical notes..." value={notes} onChange={e=>setNotes(e.target.value)}/>
                    <textarea style={S.textarea} placeholder="Exercise guidance and recommendations..." value={guidance} onChange={e=>setGuidance(e.target.value)}/>
                    <button onClick={()=>addGuidance(r.id)} style={{ ...S.btn,background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)",width:"100%" }}>Submit Guidance</button>
                  </div>
                )}
              </div>
            ))
          }
        </div>
      )}

      {/* Prescribe */}
      {activeTab==="prescribe"&&(
        <>
          <div style={S.card}>
            <div style={S.cardTitle}>Create New Prescription</div>
            <input style={S.input} placeholder="Prescription title (e.g. Week 1 Exercises)" value={presTitle} onChange={e=>setPresTitle(e.target.value)}/>
            <textarea style={{ ...S.textarea,minHeight:"120px" }}
              placeholder={"Enter exercises one per line:\nChin Tuck — 3 sets × 10 reps, hold 5s\nWall Angels — 3 sets × 10 reps\nCat Cow Stretch — 3 sets × 10 reps\nThoracic Extension — 3 sets × 8 reps"}
              value={presExs} onChange={e=>setPresExs(e.target.value)}/>
            <textarea style={S.textarea} placeholder="Clinical notes and instructions for patient..." value={presNotes} onChange={e=>setPresNotes(e.target.value)}/>
            <button onClick={createPresc} disabled={sending} style={{ ...S.btn,width:"100%",padding:"12px",background:sending?"rgba(100,100,100,0.15)":"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)",fontSize:"14px",fontWeight:"700" }}>
              {sending?"Sending...":"💊 Send Prescription to Patient"}
            </button>
          </div>

          {/* Previous prescriptions */}
          {prescs.length>0&&(
            <div style={{ marginTop:"16px" }}>
              <div style={S.cardTitle}>Previous Prescriptions</div>
              {prescs.map((p,i)=>(
                <div key={i} style={{ ...S.card,marginBottom:"12px" }}>
                  <div style={{ fontWeight:"700",fontSize:"15px",marginBottom:"8px" }}>{p.title}</div>
                  <div style={{ fontSize:"11px",color:"#475569",marginBottom:"8px" }}>{new Date(p.created_at).toLocaleDateString()}</div>
                  {p.exercises?.length>0&&p.exercises.map((ex,j)=><div key={j} style={{ padding:"6px 10px",background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.1)",borderRadius:"6px",fontSize:"13px",color:"#e2e8f0",marginBottom:"4px" }}>{ex.exercise||ex}</div>)}
                  {p.notes&&<p style={{ fontSize:"13px",color:"#94a3b8",marginTop:"8px" }}>{p.notes}</p>}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Chat Window ───────────────────────────────────────────────────────────────
function ChatWindow({ consultation, user, onBack, camState, snapshots }) {
  const [msgs,setMsgs]=useState([]),[reports,setReports]=useState([]);
  const [txt,setTxt]=useState(""),[tab,setTab]=useState("chat");
  const [sending,setSending]=useState(false);
  const endRef=useRef(null);
  const isPhysio=user.role==="physiotherapist";

  const load=useCallback(async()=>{
    try{ const r=await apiCall("get",`${API}/consult/messages/${consultation.id}`); setMsgs(r.data.messages||[]); setTimeout(()=>endRef.current?.scrollIntoView({behavior:"smooth"}),100); }catch(e){console.log("msgs",e?.response?.status);}
  },[consultation.id]);

  const loadReports=useCallback(async()=>{
    try{ const r=await apiCall("get",`${API}/consult/reports/${consultation.id}`); setReports(r.data.reports||[]); }catch{}
  },[consultation.id]);

  useEffect(()=>{ load();loadReports(); const i=setInterval(load,4000); return()=>clearInterval(i); },[load]);

  const send=async()=>{
    if(!txt.trim()||sending) return;
    setSending(true);
    try{ await apiCall("post",`${API}/consult/send-message`,{consultation_id:consultation.id,message:txt}); setTxt(""); load(); }
    catch(e){ alert("Send failed. Please logout and login again."); }
    setSending(false);
  };

  return (
    <div>
      <button onClick={onBack} style={{ ...S.btn,marginBottom:"16px",background:"rgba(255,255,255,0.05)",color:"#94a3b8",border:"1px solid rgba(255,255,255,0.08)" }}>← Back</button>
      <div style={{ ...S.card,marginBottom:"16px" }}>
        <div style={{ display:"flex",alignItems:"center",gap:"12px" }}>
          <div style={{ fontSize:"20px" }}>{isPhysio?"👤":"🏥"}</div>
          <div>
            <div style={{ fontWeight:"700" }}>{isPhysio?`Patient: ${consultation.profiles?.name||"User"}`:`Dr. ${consultation.profiles?.name||"Physiotherapist"}`}</div>
            {isPhysio&&consultation.profiles&&<div style={{ fontSize:"11px",color:"#475569" }}>{[consultation.profiles.age&&`Age:${consultation.profiles.age}`,consultation.profiles.body_weight&&`${consultation.profiles.body_weight}kg`,consultation.profiles.height&&`${consultation.profiles.height}cm`].filter(Boolean).join(" | ")}</div>}
            <span style={{ ...S.badge,background:"rgba(0,255,157,0.1)",color:"#00ff9d",fontSize:"10px" }}>{consultation.status}</span>
          </div>
        </div>
      </div>
      <div style={{ display:"flex",gap:"8px",marginBottom:"16px" }}>
        {["chat","reports"].map(t=><button key={t} onClick={()=>setTab(t)} style={{ ...S.btn,background:tab===t?"rgba(0,255,157,0.15)":"rgba(255,255,255,0.04)",color:tab===t?"#00ff9d":"#64748b",border:tab===t?"1px solid rgba(0,255,157,0.4)":"1px solid rgba(255,255,255,0.06)",textTransform:"capitalize" }}>{t}{t==="reports"&&reports.length>0&&<span style={{ ...S.badge,background:"rgba(0,255,157,0.2)",color:"#00ff9d",fontSize:"9px",marginLeft:"6px" }}>{reports.length}</span>}</button>)}
      </div>

      {tab==="chat"&&(
        <div style={S.card}>
          <div style={{ height:"340px",overflowY:"auto",marginBottom:"14px",display:"flex",flexDirection:"column",gap:"8px",padding:"4px" }}>
            {msgs.length===0&&<div style={{ textAlign:"center",color:"#334155",marginTop:"40px",fontSize:"13px" }}>No messages yet. Say hello!</div>}
            {msgs.map((m,i)=>{
              const mine=m.sender_id===localStorage.getItem("user_id");
              const isSystem=m.message_type==="system"||m.message_type==="prescription";
              return (
                <div key={i} style={{ display:"flex",justifyContent:isSystem?"center":mine?"flex-end":"flex-start" }}>
                  {isSystem
                    ?<div style={{ padding:"6px 14px",borderRadius:"20px",background:"rgba(56,189,248,0.1)",border:"1px solid rgba(56,189,248,0.2)",fontSize:"12px",color:"#38bdf8",maxWidth:"80%",textAlign:"center" }}>{m.message}</div>
                    :<div style={{ maxWidth:"72%",padding:"9px 13px",borderRadius:mine?"12px 12px 4px 12px":"12px 12px 12px 4px",background:m.message_type==="report"?"rgba(167,139,250,0.1)":mine?"rgba(0,255,157,0.12)":"rgba(255,255,255,0.06)",border:m.message_type==="report"?"1px solid rgba(167,139,250,0.3)":mine?"1px solid rgba(0,255,157,0.25)":"1px solid rgba(255,255,255,0.08)" }}>
                      <div style={{ fontSize:"10px",color:"#475569",marginBottom:"3px" }}>{m.profiles?.name||"User"}</div>
                      <div style={{ fontSize:"13px",color:m.message_type==="report"?"#a78bfa":"#e2e8f0" }}>{m.message_type==="report"?"📊 ":m.message_type==="prescription"?"💊 ":""}{m.message}</div>
                      <div style={{ fontSize:"9px",color:"#334155",marginTop:"3px" }}>{new Date(m.created_at).toLocaleTimeString()}</div>
                    </div>
                  }
                </div>
              );
            })}
            <div ref={endRef}/>
          </div>
          <div style={{ display:"flex",gap:"8px" }}>
            <input style={{ ...S.input,marginBottom:0,flex:1 }} placeholder="Type a message..." value={txt} onChange={e=>setTxt(e.target.value)} onKeyDown={e=>e.key==="Enter"&&!e.shiftKey&&send()} disabled={sending}/>
            <button onClick={send} disabled={sending||!txt.trim()} style={{ ...S.btn,background:"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)",whiteSpace:"nowrap",opacity:sending?0.6:1 }}>{sending?"...":"Send"}</button>
          </div>
        </div>
      )}

      {tab==="reports"&&(
        <div>
          {reports.length===0
            ?<div style={{ ...S.card,textAlign:"center",padding:"30px" }}><div style={{ fontSize:"36px",marginBottom:"12px" }}>📋</div><div style={{ fontWeight:"700",color:"#e2e8f0",marginBottom:"8px" }}>No Reports Yet</div><p style={{ fontSize:"13px",color:"#475569" }}>Patient hasn't shared their report yet.</p></div>
            :reports.map((r,i)=>(
              <div key={i} style={{ ...S.card,marginBottom:"12px" }}>
                <div style={{ fontWeight:"700",marginBottom:"12px" }}>Report #{i+1} — {new Date(r.created_at).toLocaleDateString()}</div>
                <div style={{ display:"flex",gap:"16px" }}>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Score</div><div style={{ fontSize:"22px",fontWeight:"900",color:scoreColor(r.posture_score||0) }}>{r.posture_score?.toFixed(0)||0}/100</div></div>
                  <div><div style={{ fontSize:"10px",color:"#475569" }}>Risk</div><div style={{ fontSize:"22px",fontWeight:"900",color:"#f87171" }}>{r.risk_score?.toFixed(0)||0}/100</div></div>
                </div>
              </div>
            ))
          }
        </div>
      )}
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [user,setUser]=useState(()=>{ const t=localStorage.getItem("token"),e=localStorage.getItem("email"); if(!t||!e) return null; return {token:t,user_id:localStorage.getItem("user_id"),email:e,name:localStorage.getItem("name"),role:localStorage.getItem("role")||"user"}; });

  const [tab,setTab]=useState("live");
  const [stats,setStats]=useState(null),[history,setHistory]=useState([]);
  const [trend,setTrend]=useState(null),[asRisk,setAsRisk]=useState(null);
  const [shap,setShap]=useState(null),[exercises,setExercises]=useState([]);
  const [mlResult,setMlResult]=useState(null),[apiOk,setApiOk]=useState(false);
  const [camState,setCamState]=useState(null),[cameraOn,setCameraOn]=useState(false);
  const [activeTimer,setActiveTimer]=useState(null);
  const [emailData,setEmailData]=useState({to:"",from:"",pass:""}),[emailStatus,setEmailStatus]=useState("");
  const [pdfLoading,setPdfLoading]=useState(false);
  const [physios,setPhysios]=useState([]),[consultations,setConsultations]=useState([]);
  const [activeChat,setActiveChat]=useState(null);
  const [activePatient,setActivePatient]=useState(null);
  const [reqMsg,setReqMsg]=useState(""),[contactStatus,setContactStatus]=useState("");
  const [snapshots,setSnapshots]=useState([]);
  const [aiAnalysis,setAiAnalysis]=useState(null),[aiLoading,setAiLoading]=useState(false);
  const [captureComplete,setCaptureComplete]=useState(false);
  const [snapshotResult,setSnapshotResult]=useState(null);
  const [prescriptions,setPrescriptions]=useState([]);
  const [showDailyLog,setShowDailyLog]=useState(false);
  const [dailyProgress,setDailyProgress]=useState([]);
  const imgRef=useRef(null);

  const isPhysio=user?.role==="physiotherapist";
  const demo={neck_forward_angle:22,shoulder_slope:14,rounded_shoulder_angle:138,pelvic_tilt:8,spine_deviation:35};

  useEffect(()=>{ if(isPhysio) setTab("patients"); else setTab("live"); },[isPhysio]);

  const loadAll=useCallback(async()=>{ try{ const [s,h,t]=await Promise.all([axios.get(`${API}/risk/stats`),axios.get(`${API}/risk/history?limit=50`),axios.get(`${API}/risk/trend`)]); setStats(s.data);setHistory(h.data.sessions||[]);setTrend(t.data);setApiOk(true); }catch{setApiOk(false);} },[]);
  const loadConsultations=useCallback(async()=>{ try{ const r=await apiCall("get",`${API}/consult/my-consultations`); setConsultations(r.data.consultations||[]); }catch{} },[]);
  const loadPhysios=useCallback(async()=>{ try{ const r=await axios.get(`${API}/consult/physiotherapists`); setPhysios(r.data.physiotherapists||[]); }catch{} },[]);
  const loadPrescriptions=useCallback(async()=>{ try{ const r=await apiCall("get",`${API}/consult/prescriptions`); setPrescriptions(r.data.prescriptions||[]); }catch{} },[]);
  const loadDailyProgress=useCallback(async()=>{ try{ const r=await apiCall("get",`${API}/consult/my-daily-progress`); setDailyProgress(r.data.tracking||[]); }catch{} },[]);

  const loadSnapshots=useCallback(async()=>{
    try { const {data,error}=await sb.storage.from("snapshots").list("",{sortBy:{column:"created_at",order:"desc"},limit:50}); if(!error&&data?.length){ const valid=data.filter(f=>f.name&&f.name!==".emptyFolderPlaceholder"&&f.name.endsWith(".jpg")); if(valid.length>0){ setSnapshots(valid.map(f=>({name:f.name,filename:f.name,url:sb.storage.from("snapshots").getPublicUrl(f.name).data.publicUrl}))); return; } } }catch{}
    try{ const r=await axios.get(`${API}/snapshots/list`); setSnapshots((r.data.snapshots||[]).map(s=>({...s,url:`${API}/snapshots/view/${s.filename||s.name}`}))); }catch{}
  },[]);

  const deleteSnapshot=async name=>{ if(!window.confirm(`Delete ${name}?`)) return; try{await sb.storage.from("snapshots").remove([name]);}catch{} try{await axios.delete(`${API}/snapshots/delete/${name}`);}catch{} loadSnapshots(); };
  const stopCamera=async()=>{ setCameraOn(false); if(imgRef.current) imgRef.current.src=""; try{await axios.post(`${API}/camera/stop`);}catch{} };

  const getAIExercises=async()=>{
    setAiLoading(true);
    try {
      let snapPaths=[];
      if(camState?.snapshot_urls?.length) snapPaths=camState.snapshot_urls.map(s=>`data/${s.filename}`);
      else if(snapshots.length) snapPaths=snapshots.slice(0,3).map(s=>`data/${s.filename||s.name}`);
      if(snapPaths.length){ const r=await axios.post(`${API}/posture/ai-analyze-snapshots`,{snapshot_paths:snapPaths,features:camState?.features||demo,result:camState?.score||{},risk:camState?.risk||{}}); if(r.data.success&&r.data.analysis?.exercises?.length){setAiAnalysis(r.data.analysis);setTab("exercises");setAiLoading(false);return;} }
      const r2=await axios.post(`${API}/posture/ai-analyze`,{features:camState?.features||demo,result:camState?.score||{},risk:camState?.risk||{}});
      if(r2.data.success&&r2.data.analysis){setAiAnalysis(r2.data.analysis);setTab("exercises");}
    }catch(e){alert("AI analysis failed: "+e.message);}
    setAiLoading(false);
  };

  useEffect(()=>{
    loadAll();loadPhysios();loadConsultations();loadSnapshots();loadPrescriptions();
    if(!isPhysio) loadDailyProgress();
    axios.post(`${API}/risk/as-risk`,demo).then(r=>setAsRisk(r.data)).catch(()=>{});
    axios.post(`${API}/posture/explain`,demo).then(r=>setShap(r.data.explanation)).catch(()=>{});
    axios.post(`${API}/posture/predict`,demo).then(r=>setMlResult(r.data)).catch(()=>{});
    axios.get(`${API}/report/exercises?features=${encodeURIComponent(JSON.stringify(demo))}`).then(r=>setExercises(r.data.exercises||[])).catch(()=>{});
    const i1=setInterval(loadAll,10000);
    const i2=setInterval(async()=>{ try{ const r=await axios.get(`${API}/camera/state`); setCamState(r.data); if(r.data.capture_done&&!captureComplete){setCaptureComplete(true);setTimeout(()=>{loadSnapshots();},3000);} }catch{} },1500);
    const i3=setInterval(loadConsultations,5000);
    const i4=setInterval(loadSnapshots,20000);
    return()=>{clearInterval(i1);clearInterval(i2);clearInterval(i3);clearInterval(i4);};
  },[]);

  const handleLogin=d=>{setUser(d);localStorage.setItem("role",d.role);};
  const handleLogout=async()=>{stopCamera();await sb.auth.signOut();localStorage.clear();setUser(null);};

  const downloadPDF=async()=>{ setPdfLoading(true); try{ const snapPaths=snapshots.slice(0,3).map(s=>`data/${s.filename||s.name}`).filter(Boolean); const res=await axios.post(`${API}/report/generate-pdf`,{features:camState?.features||demo,result:camState?.score||{},risk:camState?.risk||{},snapshot_paths:snapPaths},{responseType:"blob"}); const url=URL.createObjectURL(new Blob([res.data])); const a=document.createElement("a");a.href=url;a.download="posture_report.pdf";document.body.appendChild(a);a.click();a.remove(); }catch{alert("PDF failed.");} setPdfLoading(false); };

  const shareWhatsApp=async()=>{ await downloadPDF(); const score=camState?.score?.score||0,risk=camState?.risk?.risk_score||0,cls=camState?.score?.classification||"N/A"; const text=["PostureAI Health Report 📊","",`✅ Score: ${score}/100`,`⚠️ Risk: ${risk}/100`,`📋 Class: ${cls}`,`📸 ${snapshots.length} snapshots captured`,"","PDF saved to device — please attach it.","Generated by PostureAI"].join("%0A"); window.open(`https://wa.me/?text=${text}`,"_blank"); };

  const sendEmail=async()=>{ if(!emailData.to||!emailData.from||!emailData.pass){setEmailStatus("Fill all fields");return;} setEmailStatus("Sending..."); try{ const snapPaths=snapshots.slice(0,3).map(s=>`data/${s.filename||s.name}`).filter(Boolean); const r=await axios.post(`${API}/report/send-email`,{to_email:emailData.to,sender_email:emailData.from,sender_password:emailData.pass,features:camState?.features||demo,result:camState?.score||{},risk:camState?.risk||{},snapshot_paths:snapPaths}); setEmailStatus(r.data.success?"✅ Email sent!":"Failed"); }catch{setEmailStatus("Error");} };

  const contactPhysio=async physio=>{ if(!reqMsg.trim()){alert("Write a message first");return;} try{ const r=await apiCall("post",`${API}/consult/request`,{physio_id:physio.id,message:reqMsg}); if(r.data.success){await loadConsultations();setReqMsg("");setContactStatus("✅ Consultation requested! Physiotherapist will accept shortly.");setTimeout(()=>setContactStatus(""),6000);} }catch(e){setContactStatus("❌ "+(e.response?.data?.detail||"Error"));} };

  const grantAccess=async cid=>{ try{ await apiCall("put",`${API}/consult/grant-access/${cid}`); await loadConsultations(); alert("✅ Full access granted to physiotherapist!"); }catch(e){alert("Failed: "+e.message);} };
  const revokeAccess=async cid=>{ try{ await apiCall("put",`${API}/consult/revoke-access/${cid}`); await loadConsultations(); alert("Access revoked."); }catch{} };

  if(!user) return <LoginPage onLogin={handleLogin}/>;

  const chartData=history.slice(-20).map((h,i)=>({name:`#${i+1}`,score:parseFloat(h.posture_score)||0}));
  const shapData=(shap||[]).map(s=>({feature:s.feature,impact:parseFloat((s.shap_value||0).toFixed(3))}));
  const asData=(asRisk?.progression||[]).map(p=>({year:p.year,"No Correction":p.no_intervention,"With Exercises":p.with_intervention}));
  const classData=stats?[{name:"Good",value:stats.classifications?.GOOD||0},{name:"Warning",value:stats.classifications?.WARNING||0},{name:"Bad",value:stats.classifications?.BAD||0}]:[];
  const liveScore=camState?.score?.score||0,liveRisk=camState?.risk?.risk_score||0,liveClass=camState?.score?.classification||"—";

  const tabs=isPhysio?[
    {id:"patients",label:"My Patients"},
    {id:"dashboard",label:"Dashboard"},
  ]:[
    {id:"live",label:"Live Camera"},
    {id:"dashboard",label:"Dashboard"},
    {id:"snapshots",label:`Snapshots${snapshots.length?` (${snapshots.length})`:""}`},
    {id:"history",label:"History"},
    {id:"risk",label:"AS Risk"},
    {id:"shap",label:"SHAP AI"},
    {id:"exercises",label:"Exercises"},
    {id:"physiotherapists",label:"Physiotherapists"},
    {id:"find-doctors",label:"Find Doctors"},
    {id:"report",label:"Reports"},
  ];

  // Full screen views
  if(activeChat) return (
    <div style={S.app}>
      <div style={S.header}><div><h1 style={S.title}>PostureAI</h1></div><button onClick={handleLogout} style={{ ...S.btn,background:"rgba(248,113,113,0.1)",color:"#f87171",border:"1px solid rgba(248,113,113,0.3)" }}>Logout</button></div>
      <ChatWindow consultation={activeChat} user={user} onBack={()=>setActiveChat(null)} camState={camState} snapshots={snapshots}/>
    </div>
  );

  if(activePatient&&isPhysio) return (
    <div style={S.app}>
      <div style={S.header}><div><h1 style={S.title}>PostureAI</h1><p style={S.subtitle}>🏥 Patient View</p></div><button onClick={handleLogout} style={{ ...S.btn,background:"rgba(248,113,113,0.1)",color:"#f87171",border:"1px solid rgba(248,113,113,0.3)" }}>Logout</button></div>
      <PatientProgress consultation={activePatient} physio={user} onBack={()=>setActivePatient(null)}/>
    </div>
  );

  return (
    <div style={S.app}>
      {activeTimer&&<ExerciseTimer exercise={activeTimer} onDone={()=>setActiveTimer(null)}/>}
      {showDailyLog&&<DailyLogModal camState={camState} consultations={consultations} prescriptions={prescriptions} onClose={()=>setShowDailyLog(false)} onLogged={()=>{loadDailyProgress();}}/>}
      <VoiceCamera camState={camState}/>

      <div style={S.header}>
        <div>
          <h1 style={S.title}>PostureAI</h1>
          <p style={S.subtitle}>{isPhysio?"🏥 Physiotherapist":"👤 Patient"} — {user.name||user.email}</p>
        </div>
        <div style={{ display:"flex",alignItems:"center",gap:"10px",flexWrap:"wrap" }}>
          <span style={{ width:"8px",height:"8px",borderRadius:"50%",display:"inline-block",background:apiOk?"#00ff9d":"#f87171",boxShadow:apiOk?"0 0 8px #00ff9d":"0 0 8px #f87171" }}/>
          <span style={{ fontSize:"12px",color:apiOk?"#00ff9d":"#f87171" }}>{apiOk?"Connected":"Offline"}</span>
          {!isPhysio&&<button onClick={()=>setShowDailyLog(true)} style={{ ...S.btn,background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"12px" }}>📅 Log Today</button>}
          {!isPhysio&&<button onClick={downloadPDF} disabled={pdfLoading} style={{ ...S.btn,background:"rgba(100,100,100,0.1)",color:"#94a3b8",border:"1px solid rgba(100,100,100,0.3)",fontSize:"12px" }}>{pdfLoading?"...":"PDF"}</button>}
          {!isPhysio&&<button onClick={shareWhatsApp} disabled={pdfLoading} style={{ ...S.btn,background:"rgba(37,211,102,0.1)",color:"#25d366",border:"1px solid rgba(37,211,102,0.3)",fontSize:"12px" }}>WhatsApp</button>}
          <button onClick={handleLogout} style={{ ...S.btn,background:"rgba(248,113,113,0.1)",color:"#f87171",border:"1px solid rgba(248,113,113,0.3)",fontSize:"12px" }}>Logout</button>
        </div>
      </div>

      <div style={{ display:"flex",gap:"6px",marginBottom:"20px",flexWrap:"wrap" }}>
        {tabs.map(t=><button key={t.id} onClick={()=>setTab(t.id)} style={{ ...S.btn,background:tab===t.id?"rgba(0,255,157,0.15)":"rgba(255,255,255,0.04)",color:tab===t.id?"#00ff9d":"#64748b",border:tab===t.id?"1px solid rgba(0,255,157,0.4)":"1px solid rgba(255,255,255,0.06)",fontSize:"12px",padding:"6px 14px" }}>{t.label}</button>)}
      </div>

      {/* ── LIVE CAMERA ──────────────────────────────────────────────────── */}
      {tab==="live"&&!isPhysio&&(
        <>
          <div style={S.grid}>
            <div style={S.card}>
              <div style={S.cardTitle}>Live Posture Score</div>
              <RingScore score={liveScore}/>
              <div style={{ textAlign:"center",marginTop:"12px" }}><span style={{ ...S.badge,background:`${classColor(liveClass)}22`,color:classColor(liveClass) }}>{liveClass}</span></div>
            </div>
            <div style={S.card}>
              <div style={S.cardTitle}>Capture Progress</div>
              <div style={{ display:"flex",gap:"12px",justifyContent:"center",marginBottom:"14px" }}>
                {["FRONT","LEFT","RIGHT"].map((side,i)=>(
                  <div key={side} style={{ textAlign:"center" }}>
                    <div style={{ width:44,height:44,borderRadius:"50%",margin:"0 auto 6px",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"12px",fontWeight:"700",background:(camState?.saved_paths?.length||0)>i?"rgba(0,255,157,0.2)":camState?.current_step===i?"rgba(0,255,157,0.08)":"rgba(255,255,255,0.04)",border:(camState?.saved_paths?.length||0)>i?"2px solid #00ff9d":camState?.current_step===i?"2px solid rgba(0,255,157,0.5)":"2px solid rgba(255,255,255,0.08)",color:(camState?.saved_paths?.length||0)>i?"#00ff9d":camState?.current_step===i?"#00ff9d":"#334155" }}>
                      {(camState?.saved_paths?.length||0)>i?"✓":i+1}
                    </div>
                    <div style={{ fontSize:"9px",color:"#475569" }}>{side}</div>
                  </div>
                ))}
              </div>
              <div style={{ fontSize:"13px",color:"#94a3b8",textAlign:"center",marginBottom:"12px" }}>
                {camState?.capture_done?"✅ All 3 snapshots captured!":camState?.instruction||"Start camera to begin"}
              </div>
              {camState?.capture_done&&<button onClick={getAIExercises} disabled={aiLoading} style={{ ...S.btn,width:"100%",marginBottom:"8px",padding:"12px",background:aiLoading?"rgba(100,100,100,0.15)":"rgba(167,139,250,0.2)",color:"#a78bfa",border:"1px solid rgba(167,139,250,0.5)",fontSize:"13px",fontWeight:"700" }}>{aiLoading?"🤖 Analyzing...":"🤖 Get AI Exercise Recommendations"}</button>}
              <button onClick={async()=>{await axios.post(`${API}/camera/reset`);setCameraOn(false);setCaptureComplete(false);}} style={{ ...S.btn,width:"100%",background:"rgba(255,255,255,0.04)",color:"#64748b",border:"1px solid rgba(255,255,255,0.08)",fontSize:"12px" }}>Reset</button>
            </div>
            <div style={S.card}>
              <div style={S.cardTitle}>Live Spinal Risk</div>
              <p style={{ ...S.statNum,color:scoreColor(100-liveRisk) }}>{liveRisk}<span style={{ fontSize:"16px",color:"#475569" }}>/100</span></p>
              <p style={{ fontSize:"12px",color:"#475569",marginTop:"8px" }}>{camState?.risk?.severity||"—"}</p>
              <button onClick={()=>setShowDailyLog(true)} style={{ ...S.btn,width:"100%",marginTop:"12px",background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"12px" }}>📅 Log Today's Progress</button>
            </div>
          </div>
          <div style={S.card}>
            <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"12px" }}>
              <div style={S.cardTitle}>Live Camera</div>
              {cameraOn&&<span style={{ ...S.badge,background:"rgba(0,255,157,0.1)",color:"#00ff9d" }}>● LIVE</span>}
            </div>
            {!cameraOn
              ?<div style={{ display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",minHeight:"360px",gap:"20px",background:"rgba(0,0,0,0.3)",borderRadius:"8px" }}>
                <div style={{ fontSize:"60px" }}>📷</div>
                <div style={{ fontSize:"15px",color:"#475569",textAlign:"center" }}>Camera is off<br/><span style={{ fontSize:"12px" }}>Auto-captures FRONT → LEFT → RIGHT</span></div>
                <button onClick={()=>setCameraOn(true)} style={{ ...S.btn,padding:"14px 40px",fontSize:"16px",background:"rgba(0,255,157,0.15)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.4)" }}>Start Camera</button>
              </div>
              :<div style={{ position:"relative" }}>
                <img ref={imgRef} key={cameraOn?"on":"off"} src={cameraOn?`${API}/camera/stream`:""} alt="Live" style={{ maxWidth:"100%",maxHeight:"520px",borderRadius:"8px",display:"block",margin:"0 auto" }} onError={e=>{e.target.style.display="none";}}/>
                <button onClick={stopCamera} style={{ ...S.btn,position:"absolute",top:"10px",left:"10px",background:"rgba(248,113,113,0.85)",color:"white",border:"none",fontSize:"12px",padding:"6px 12px" }}>■ Stop</button>
                <div style={{ position:"absolute",top:"10px",right:"10px",background:"rgba(0,0,0,0.7)",padding:"4px 10px",borderRadius:"6px",fontSize:"11px",color:"#00ff9d" }}>PostureAI</div>
              </div>
            }
          </div>
          {aiAnalysis&&(
            <div style={{ ...S.card,marginTop:"16px",borderColor:"rgba(167,139,250,0.3)" }}>
              <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"12px" }}>
                <div style={S.cardTitle}>🤖 AI Exercise Recommendations</div>
                <span style={{ ...S.badge,background:"rgba(167,139,250,0.15)",color:"#a78bfa" }}>Claude AI</span>
              </div>
              {aiAnalysis.summary&&<div style={{ padding:"12px",background:"rgba(167,139,250,0.05)",border:"1px solid rgba(167,139,250,0.2)",borderRadius:"8px",marginBottom:"14px" }}><p style={{ fontSize:"13px",color:"#c4b5fd",margin:0,lineHeight:"1.6" }}>{aiAnalysis.summary}</p></div>}
              <div style={S.grid}>{(aiAnalysis.exercises||[]).map((ex,i)=><AICard key={i} ex={ex} onStart={setActiveTimer}/>)}</div>
              {aiAnalysis.lifestyle_tips?.length>0&&<div style={{ marginTop:"12px" }}>{aiAnalysis.lifestyle_tips.map((t,i)=><div key={i} style={{ padding:"8px 12px",marginBottom:"6px",background:"rgba(56,189,248,0.05)",border:"1px solid rgba(56,189,248,0.1)",borderRadius:"6px",fontSize:"13px",color:"#94a3b8" }}>{i+1}. {t}</div>)}</div>}
            </div>
          )}
        </>
      )}

      {/* ── SNAPSHOTS ────────────────────────────────────────────────────── */}
      {tab==="snapshots"&&!isPhysio&&(
        <>
          <SnapshotManager snapshots={snapshots} onDelete={deleteSnapshot} onAnalyze={r=>setSnapshotResult(r)} onRefresh={loadSnapshots}/>
          {snapshotResult&&(
            <div style={{ ...S.card,marginTop:"16px" }}>
              <div style={S.cardTitle}>🤖 AI Analysis</div>
              {snapshotResult.ai_analysis?.summary&&<p style={{ fontSize:"13px",color:"#c4b5fd",marginBottom:"12px" }}>{snapshotResult.ai_analysis.summary}</p>}
              {snapshotResult.ai_analysis?.exercises?.length>0&&<div style={S.grid}>{snapshotResult.ai_analysis.exercises.map((ex,i)=><AICard key={i} ex={ex} onStart={setActiveTimer}/>)}</div>}
              <ShareReportPanel camState={{features:snapshotResult.features,score:snapshotResult.score,risk:snapshotResult.risk}} consultations={consultations} snapshots={snapshots}/>
            </div>
          )}
        </>
      )}

      {/* ── DASHBOARD ────────────────────────────────────────────────────── */}
      {tab==="dashboard"&&(
        isPhysio?(
          <>
            <div style={S.grid}>
              <div style={S.card}><div style={S.cardTitle}>Total Patients</div><p style={{ ...S.statNum,color:"#38bdf8" }}>{consultations.length}</p></div>
              <div style={S.card}><div style={S.cardTitle}>Pending</div><p style={{ ...S.statNum,color:"#fbbf24" }}>{consultations.filter(c=>c.status==="pending").length}</p></div>
              <div style={S.card}><div style={S.cardTitle}>Active</div><p style={{ ...S.statNum,color:"#00ff9d" }}>{consultations.filter(c=>c.status==="active").length}</p></div>
            </div>
          </>
        ):(
          <>
            <div style={S.grid}>
              {[{title:"Avg Score",value:stats?.avg_score||0,unit:"/100",color:scoreColor(stats?.avg_score||0)},{title:"Sessions",value:stats?.total_sessions||0,color:"#38bdf8"},{title:"Best",value:stats?.best_score||0,unit:"/100",color:"#00ff9d"},{title:"Latest",value:stats?.latest_score||0,unit:"/100",color:scoreColor(stats?.latest_score||0)}].map((item,i)=>(
                <div key={i} style={S.card}><div style={S.cardTitle}>{item.title}</div><p style={{ ...S.statNum,color:item.color }}>{item.value}<span style={{ fontSize:"16px",color:"#475569" }}>{item.unit}</span></p></div>
              ))}
            </div>
            {/* Daily progress chart */}
            {dailyProgress.length>0&&(
              <div style={{ ...S.card,marginBottom:"16px" }}>
                <div style={S.cardTitle}>My Daily Progress ({dailyProgress.length} days tracked)</div>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={dailyProgress.map(d=>({date:d.date,score:d.posture_score||0,risk:d.risk_score||0}))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)"/>
                    <XAxis dataKey="date" tick={{ fill:"#475569",fontSize:9 }} axisLine={false}/>
                    <YAxis domain={[0,100]} tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                    <Tooltip content={<CustomTip/>}/>
                    <Legend wrapperStyle={{ fontSize:"12px",color:"#94a3b8" }}/>
                    <Line type="monotone" dataKey="score" name="Posture Score" stroke="#00ff9d" strokeWidth={2} dot={{ r:3 }}/>
                    <Line type="monotone" dataKey="risk" name="Risk Score" stroke="#f87171" strokeWidth={2} dot={{ r:3 }}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
            <div style={{ ...S.grid,gridTemplateColumns:"1fr 2fr" }}>
              <div style={{ ...S.card,display:"flex",flexDirection:"column",alignItems:"center",gap:"16px" }}>
                <div style={S.cardTitle}>Posture Score</div>
                <RingScore score={stats?.avg_score||0}/>
                {trend&&<span style={{ fontSize:"18px",fontWeight:"700",color:trend.trend==="IMPROVING"?"#00ff9d":trend.trend==="WORSENING"?"#f87171":"#fbbf24" }}>{trend.trend==="IMPROVING"?"↑":trend.trend==="WORSENING"?"↓":"→"} {trend.trend}</span>}
              </div>
              <div style={S.card}>
                <div style={S.cardTitle}>Score History</div>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={chartData}>
                    <defs><linearGradient id="sg" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#00ff9d" stopOpacity={0.3}/><stop offset="95%" stopColor="#00ff9d" stopOpacity={0}/></linearGradient></defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)"/>
                    <XAxis dataKey="name" tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                    <YAxis domain={[0,100]} tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                    <Tooltip content={<CustomTip/>}/>
                    <Area type="monotone" dataKey="score" name="Score" stroke="#00ff9d" fill="url(#sg)" strokeWidth={2}/>
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )
      )}

      {/* ── HISTORY ──────────────────────────────────────────────────────── */}
      {tab==="history"&&!isPhysio&&(
        <div style={S.card}>
          <div style={S.cardTitle}>Session History ({history.length})</div>
          <div style={{ overflowX:"auto" }}>
            <table style={S.table}>
              <thead><tr>{["Timestamp","Score","Class","Neck","Shoulder","Spine"].map(h=><th key={h} style={S.th}>{h}</th>)}</tr></thead>
              <tbody>{history.slice().reverse().map((row,i)=>(
                <tr key={i} style={{ background:i%2===0?"rgba(255,255,255,0.01)":"transparent" }}>
                  <td style={S.td}>{row.timestamp}</td>
                  <td style={{ ...S.td,color:scoreColor(parseFloat(row.posture_score)),fontWeight:"700" }}>{parseFloat(row.posture_score).toFixed(0)}</td>
                  <td style={S.td}><span style={{ ...S.badge,background:`${classColor(row.classification)}22`,color:classColor(row.classification) }}>{row.classification}</span></td>
                  <td style={S.td}>{parseFloat(row.neck_forward_angle||0).toFixed(1)}</td>
                  <td style={S.td}>{parseFloat(row.shoulder_slope||0).toFixed(1)}</td>
                  <td style={S.td}>{parseFloat(row.spine_deviation||0).toFixed(1)}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── AS RISK ──────────────────────────────────────────────────────── */}
      {tab==="risk"&&!isPhysio&&asRisk&&(
        <>
          <div style={S.grid}>
            <div style={{ ...S.card,borderColor:asRisk.color+"44" }}>
              <div style={S.cardTitle}>AS Risk Score</div>
              <p style={{ ...S.statNum,color:asRisk.color }}>{asRisk.as_score}</p>
              <span style={{ ...S.badge,background:asRisk.color+"22",color:asRisk.color }}>Stage {asRisk.stage} — {asRisk.stage_name}</span>
              <p style={{ fontSize:"13px",color:"#94a3b8",marginTop:"12px" }}>{asRisk.description}</p>
            </div>
            <div style={S.card}>
              <div style={S.cardTitle}>Risk Indicators</div>
              {asRisk.indicators?.length>0?asRisk.indicators.map((ind,i)=><div key={i} style={{ padding:"8px 12px",marginBottom:"8px",background:"rgba(248,113,113,0.08)",border:"1px solid rgba(248,113,113,0.2)",borderRadius:"6px",fontSize:"13px",color:"#fca5a5" }}>! {ind}</div>):<p style={{ color:"#00ff9d",fontSize:"13px" }}>No risk indicators!</p>}
            </div>
          </div>
          <div style={S.card}>
            <div style={S.cardTitle}>10-Year Progression</div>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={asData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)"/>
                <XAxis dataKey="year" tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                <YAxis domain={[0,100]} tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                <Tooltip content={<CustomTip/>}/>
                <Legend wrapperStyle={{ fontSize:"12px",color:"#94a3b8" }}/>
                <Line type="monotone" dataKey="No Correction" stroke="#f87171" strokeWidth={2} dot={false}/>
                <Line type="monotone" dataKey="With Exercises" stroke="#00ff9d" strokeWidth={2} dot={false} strokeDasharray="5 5"/>
              </LineChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* ── SHAP ─────────────────────────────────────────────────────────── */}
      {tab==="shap"&&!isPhysio&&(
        <>
          {mlResult&&<div style={S.grid}>
            <div style={S.card}><div style={S.cardTitle}>ML Prediction</div><p style={{ ...S.statNum,fontSize:"28px",color:classColor(mlResult.prediction) }}>{mlResult.prediction}</p><p style={{ color:"#475569",fontSize:"12px" }}>Confidence: {mlResult.confidence}%</p></div>
            <div style={S.card}><div style={S.cardTitle}>Probabilities</div>{mlResult.probabilities&&Object.entries(mlResult.probabilities).map(([k,v])=>(
              <div key={k} style={{ marginBottom:"10px" }}>
                <div style={{ display:"flex",justifyContent:"space-between",marginBottom:"4px" }}><span style={{ fontSize:"12px",color:"#94a3b8" }}>{k}</span><span style={{ fontSize:"12px",color:classColor(k),fontWeight:"700" }}>{v}%</span></div>
                <div style={{ height:"4px",background:"rgba(255,255,255,0.06)",borderRadius:"2px" }}><div style={{ height:"100%",width:`${v}%`,background:classColor(k),borderRadius:"2px" }}/></div>
              </div>
            ))}</div>
          </div>}
          <div style={S.card}>
            <div style={S.cardTitle}>SHAP Feature Impact</div>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={shapData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)"/>
                <XAxis type="number" tick={{ fill:"#475569",fontSize:10 }} axisLine={false}/>
                <YAxis type="category" dataKey="feature" tick={{ fill:"#94a3b8",fontSize:11 }} axisLine={false} width={130}/>
                <Tooltip content={<CustomTip/>}/>
                <Bar dataKey="impact" name="SHAP Impact" radius={[0,6,6,0]} fill="#38bdf8"/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* ── EXERCISES ────────────────────────────────────────────────────── */}
      {tab==="exercises"&&!isPhysio&&(
        <>
          {/* Doctor prescribed exercises */}
          {prescriptions.length>0&&(
            <div style={{ marginBottom:"20px" }}>
              <div style={S.cardTitle}>💊 Prescribed by Your Physiotherapist</div>
              {prescriptions.map((p,i)=>(
                <div key={i} style={{ ...S.card,marginBottom:"12px",borderColor:"rgba(56,189,248,0.3)" }}>
                  <div style={{ fontWeight:"700",fontSize:"15px",marginBottom:"4px" }}>{p.title}</div>
                  <div style={{ fontSize:"12px",color:"#475569",marginBottom:"10px" }}>By: {p.profiles?.name||"Physiotherapist"} — {new Date(p.created_at).toLocaleDateString()}</div>
                  {p.notes&&<p style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"10px" }}>{p.notes}</p>}
                  <div style={S.grid}>
                    {(p.exercises||[]).map((ex,j)=>{
                      const exName=ex.exercise||ex.name||ex;
                      return (
                        <div key={j} style={S.card}>
                          <div style={{ fontWeight:"700",marginBottom:"8px",color:"#38bdf8" }}>{exName}</div>
                          <div style={{ display:"flex",gap:"6px",marginBottom:"8px" }}>
                            {[{l:"Sets",v:ex.sets||3},{l:"Reps",v:ex.reps||10},{l:"Hold",v:`${ex.hold_secs||5}s`}].map(item=>(
                              <div key={item.l} style={{ flex:1,background:"rgba(255,255,255,0.04)",borderRadius:"6px",padding:"6px",textAlign:"center" }}>
                                <div style={{ fontSize:"14px",fontWeight:"700",color:"#38bdf8" }}>{item.v}</div>
                                <div style={{ fontSize:"9px",color:"#475569" }}>{item.l}</div>
                              </div>
                            ))}
                          </div>
                          <button onClick={()=>setActiveTimer({name:exName,exercise:exName,...ex})} style={{ ...S.btn,width:"100%",background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"12px" }}>Start Timer</button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* AI recommendations */}
          {aiAnalysis?.exercises?.length>0&&(
            <div style={{ marginBottom:"20px" }}>
              <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"12px" }}>
                <div style={S.cardTitle}>🤖 AI Recommendations</div>
                <span style={{ ...S.badge,background:"rgba(167,139,250,0.15)",color:"#a78bfa" }}>Claude AI</span>
              </div>
              {aiAnalysis.summary&&<div style={{ ...S.card,marginBottom:"12px",borderColor:"rgba(167,139,250,0.2)" }}><p style={{ fontSize:"13px",color:"#c4b5fd",margin:0 }}>{aiAnalysis.summary}</p></div>}
              <div style={S.grid}>{aiAnalysis.exercises.map((ex,i)=><AICard key={i} ex={ex} onStart={setActiveTimer}/>)}</div>
            </div>
          )}

          {!aiAnalysis&&!prescriptions.length&&(
            <div style={{ ...S.card,marginBottom:"16px",textAlign:"center",padding:"24px" }}>
              <div style={{ fontSize:"32px",marginBottom:"8px" }}>🤖</div>
              <p style={{ color:"#475569",fontSize:"13px",marginBottom:"12px" }}>Capture posture in Live Camera or contact a physiotherapist for exercises.</p>
              <button onClick={getAIExercises} disabled={aiLoading} style={{ ...S.btn,background:"rgba(167,139,250,0.1)",color:"#a78bfa",border:"1px solid rgba(167,139,250,0.3)",padding:"10px 20px" }}>{aiLoading?"Analyzing...":"🤖 Get AI Recommendations"}</button>
            </div>
          )}

          {/* Standard exercises */}
          <div style={S.cardTitle}>Standard Exercises</div>
          <div style={S.grid}>{exercises.length===0?<div style={S.card}><p style={{ color:"#00ff9d" }}>Great posture!</p></div>
          :exercises.map((ex,i)=>(
            <div key={i} style={S.card}>
              <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"10px" }}><div style={{ fontSize:"14px",fontWeight:"700" }}>{ex.exercise}</div><span style={{ ...S.badge,background:ex.difficulty==="Easy"?"rgba(0,255,157,0.1)":"rgba(251,191,36,0.1)",color:ex.difficulty==="Easy"?"#00ff9d":"#fbbf24" }}>{ex.difficulty}</span></div>
              <p style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"10px" }}>{ex.description}</p>
              <div style={{ display:"flex",gap:"8px",marginBottom:"10px" }}>{[{l:"Sets",v:ex.sets},{l:"Reps",v:ex.reps},{l:"Hold",v:`${ex.hold_secs}s`}].map(item=><div key={item.l} style={{ flex:1,background:"rgba(255,255,255,0.04)",borderRadius:"8px",padding:"8px",textAlign:"center" }}><div style={{ fontSize:"18px",fontWeight:"700",color:"#00ff9d" }}>{item.v}</div><div style={{ fontSize:"10px",color:"#475569" }}>{item.l}</div></div>)}</div>
              <button onClick={()=>setActiveTimer(ex)} style={{ ...S.btn,width:"100%",background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)" }}>Start Timer</button>
            </div>
          ))}</div>
        </>
      )}

      {/* ── PHYSIOTHERAPISTS (Patient) ────────────────────────────────────── */}
      {tab==="physiotherapists"&&!isPhysio&&(
        <>
          {/* My consultations with access control */}
          {consultations.length>0&&(
            <div style={{ marginBottom:"24px" }}>
              <div style={S.cardTitle}>My Consultations</div>
              {consultations.map((c,i)=>(
                <div key={i} style={{ ...S.card,marginBottom:"12px",borderColor:c.access_granted?"rgba(0,255,157,0.3)":"rgba(255,255,255,0.08)" }}>
                  <div style={{ display:"flex",justifyContent:"space-between",alignItems:"flex-start",flexWrap:"wrap",gap:"10px" }}>
                    <div>
                      <div style={{ fontWeight:"700",marginBottom:"4px",fontSize:"15px" }}>🏥 Dr. {c.profiles?.name||"Physiotherapist"}</div>
                      <div style={{ fontSize:"12px",color:"#475569",marginBottom:"4px" }}>{c.profiles?.speciality}</div>
                      {c.profiles?.license_number&&<div style={{ fontSize:"11px",color:"#334155",marginBottom:"4px" }}>License: {c.profiles.license_number}</div>}
                      <div style={{ display:"flex",gap:"6px",flexWrap:"wrap",marginTop:"6px" }}>
                        <span style={{ ...S.badge,background:c.status==="active"?"rgba(0,255,157,0.1)":"rgba(251,191,36,0.1)",color:c.status==="active"?"#00ff9d":"#fbbf24" }}>{c.status}</span>
                        {c.access_granted
                          ?<span style={{ ...S.badge,background:"rgba(0,255,157,0.15)",color:"#00ff9d" }}>🔓 Full Access Granted</span>
                          :<span style={{ ...S.badge,background:"rgba(251,191,36,0.1)",color:"#fbbf24" }}>🔒 Basic Access</span>
                        }
                      </div>
                    </div>
                    <div style={{ display:"flex",flexDirection:"column",gap:"6px" }}>
                      {c.status==="active"&&(
                        <button onClick={()=>setActiveChat(c)} style={{ ...S.btn,background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"12px" }}>💬 Chat</button>
                      )}
                      {c.status==="active"&&!c.access_granted&&(
                        <button onClick={()=>grantAccess(c.id)} style={{ ...S.btn,background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)",fontSize:"12px" }}>🔓 Grant Full Access</button>
                      )}
                      {c.access_granted&&(
                        <button onClick={()=>revokeAccess(c.id)} style={{ ...S.btn,background:"rgba(248,113,113,0.1)",color:"#f87171",border:"1px solid rgba(248,113,113,0.3)",fontSize:"11px" }}>Revoke Access</button>
                      )}
                    </div>
                  </div>
                  {c.status==="pending"&&<div style={{ marginTop:"8px",fontSize:"12px",color:"#fbbf24",padding:"6px 10px",background:"rgba(251,191,36,0.05)",border:"1px solid rgba(251,191,36,0.15)",borderRadius:"6px" }}>⏳ Waiting for physiotherapist to accept your request</div>}
                  {c.access_granted&&<div style={{ marginTop:"8px",fontSize:"12px",color:"#00ff9d",padding:"6px 10px",background:"rgba(0,255,157,0.05)",border:"1px solid rgba(0,255,157,0.15)",borderRadius:"6px" }}>✅ Your physiotherapist can view your full posture history and progress charts</div>}
                </div>
              ))}
              {/* Share report */}
              <ShareReportPanel camState={camState} consultations={consultations} snapshots={snapshots}/>
            </div>
          )}

          {/* Status message */}
          {contactStatus&&<div style={{ padding:"12px 16px",marginBottom:"16px",borderRadius:"8px",fontSize:"13px",background:contactStatus.includes("✅")?"rgba(0,255,157,0.08)":"rgba(248,113,113,0.1)",border:`1px solid ${contactStatus.includes("✅")?"rgba(0,255,157,0.3)":"rgba(248,113,113,0.3)"}`,color:contactStatus.includes("✅")?"#00ff9d":"#f87171" }}>{contactStatus}</div>}

          {/* Available physios */}
          <div style={S.cardTitle}>Available Physiotherapists</div>
          <div style={{ ...S.card,marginBottom:"16px" }}>
            <div style={{ fontSize:"12px",color:"#475569",marginBottom:"8px" }}>Your message (sent with request):</div>
            <textarea style={S.textarea} placeholder="Describe your posture issues and what help you need..." value={reqMsg} onChange={e=>setReqMsg(e.target.value)}/>
          </div>
          {!physios.length
            ?<div style={{ ...S.card,textAlign:"center",padding:"24px" }}><div style={{ fontSize:"32px",marginBottom:"12px" }}>🏥</div><div style={{ fontWeight:"700",marginBottom:"8px" }}>No Physiotherapists Registered</div><p style={{ fontSize:"13px",color:"#475569" }}>Ask your physiotherapist to register on PostureAI.</p></div>
            :<div style={S.grid}>{physios.map((p,i)=>(
              <div key={i} style={S.card}>
                <div style={{ display:"flex",alignItems:"center",gap:"12px",marginBottom:"12px" }}>
                  <div style={{ width:48,height:48,borderRadius:"50%",background:"rgba(0,255,157,0.1)",border:"2px solid rgba(0,255,157,0.3)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:"20px" }}>🏥</div>
                  <div><div style={{ fontWeight:"700",fontSize:"15px" }}>{p.name||"Dr. Unknown"}</div><div style={{ fontSize:"12px",color:"#475569" }}>{p.speciality||"Physiotherapist"}</div></div>
                </div>
                {p.experience&&<div style={{ fontSize:"12px",color:"#64748b",marginBottom:"4px" }}>Exp: {p.experience} years</div>}
                {p.license_number&&<div style={{ fontSize:"11px",color:"#334155",marginBottom:"8px" }}>License: {p.license_number}</div>}
                {consultations.some(c=>c.physio_id===p.id)
                  ?<div style={{ padding:"8px 12px",background:"rgba(0,255,157,0.08)",border:"1px solid rgba(0,255,157,0.2)",borderRadius:"8px",fontSize:"12px",color:"#00ff9d",textAlign:"center" }}>✓ Contacted ({consultations.find(c=>c.physio_id===p.id)?.status})</div>
                  :<button onClick={()=>contactPhysio(p)} style={{ ...S.btn,width:"100%",padding:"10px",background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)" }}>Contact Physiotherapist</button>
                }
              </div>
            ))}</div>
          }
        </>
      )}

      {/* ── MY PATIENTS (Physio) ──────────────────────────────────────────── */}
      {tab==="patients"&&isPhysio&&(
        <>
          <div style={S.cardTitle}>My Patients ({consultations.length})</div>
          {!consultations.length
            ?<div style={{ ...S.card,textAlign:"center",padding:"30px" }}><div style={{ fontSize:"32px",marginBottom:"12px" }}>👥</div><div style={{ fontWeight:"700",marginBottom:"8px" }}>No Patients Yet</div><p style={{ fontSize:"13px",color:"#475569" }}>Patients will contact you from the Physiotherapists section.</p></div>
            :consultations.map((c,i)=>(
              <div key={i} style={{ ...S.card,marginBottom:"12px",borderColor:c.access_granted?"rgba(0,255,157,0.3)":"rgba(255,255,255,0.08)" }}>
                <div style={{ display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:"10px" }}>
                  <div>
                    <div style={{ fontWeight:"700",marginBottom:"4px",fontSize:"15px" }}>👤 {c.profiles?.name||"Patient"}</div>
                    {c.profiles&&<div style={{ fontSize:"12px",color:"#475569",marginBottom:"4px" }}>{[c.profiles.age&&`Age:${c.profiles.age}`,c.profiles.body_weight&&`${c.profiles.body_weight}kg`,c.profiles.height&&`${c.profiles.height}cm`].filter(Boolean).join(" | ")}</div>}
                    <div style={{ fontSize:"12px",color:"#64748b",marginBottom:"8px",fontStyle:"italic" }}>{c.user_message}</div>
                    <div style={{ display:"flex",gap:"6px",flexWrap:"wrap" }}>
                      <span style={{ ...S.badge,background:c.status==="active"?"rgba(0,255,157,0.1)":"rgba(251,191,36,0.1)",color:c.status==="active"?"#00ff9d":"#fbbf24" }}>{c.status}</span>
                      {c.access_granted?<span style={{ ...S.badge,background:"rgba(0,255,157,0.15)",color:"#00ff9d" }}>🔓 Full Access</span>:<span style={{ ...S.badge,background:"rgba(251,191,36,0.1)",color:"#fbbf24" }}>🔒 Basic</span>}
                    </div>
                  </div>
                  <div style={{ display:"flex",gap:"8px",flexWrap:"wrap" }}>
                    {c.status==="pending"&&<button onClick={async()=>{await apiCall("put",`${API}/consult/update-status/${c.id}`,{status:"active"});loadConsultations();}} style={{ ...S.btn,background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)" }}>Accept</button>}
                    {c.status==="active"&&<button onClick={()=>setActiveChat(c)} style={{ ...S.btn,background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"12px" }}>💬 Chat</button>}
                    {c.status==="active"&&<button onClick={()=>setActivePatient(c)} style={{ ...S.btn,background:"rgba(167,139,250,0.1)",color:"#a78bfa",border:"1px solid rgba(167,139,250,0.3)",fontSize:"12px" }}>📊 View Progress</button>}
                  </div>
                </div>
                {!c.access_granted&&c.status==="active"&&<div style={{ marginTop:"8px",padding:"6px 10px",background:"rgba(251,191,36,0.05)",border:"1px solid rgba(251,191,36,0.15)",borderRadius:"6px",fontSize:"11px",color:"#fbbf24" }}>⚠️ Patient hasn't granted full access yet. You can still see shared reports and daily logs.</div>}
              </div>
            ))
          }
        </>
      )}

      {/* ── FIND DOCTORS ─────────────────────────────────────────────────── */}
      {tab==="find-doctors"&&!isPhysio&&<NearbyDoctors/>}

      {/* ── REPORTS ──────────────────────────────────────────────────────── */}
      {tab==="report"&&!isPhysio&&(
        <>
          {snapshots.length>0&&(
            <div style={{ ...S.card,marginBottom:"16px" }}>
              <div style={S.cardTitle}>Captured Snapshots</div>
              <div style={{ display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:"10px" }}>
                {snapshots.slice(0,3).map((snap,i)=>{ const url=snap.url||snap.storage_url||`${API}/snapshots/view/${snap.filename||snap.name}`; const sides=["Front","Left Side","Right Side"]; return (<div key={i}><BigImage src={url} fallbackSrc={`${API}/snapshots/view/${snap.filename||snap.name}`} label={sides[i]}/><div style={{ fontSize:"11px",color:"#475569",textAlign:"center",marginTop:"4px" }}>{sides[i]}</div></div>); })}
              </div>
            </div>
          )}
          <div style={S.grid}>
            <div style={S.card}>
              <div style={S.cardTitle}>Download PDF</div>
              <p style={{ fontSize:"13px",color:"#94a3b8",marginBottom:"12px" }}>Includes all snapshots, posture analysis & exercises.</p>
              <button onClick={downloadPDF} disabled={pdfLoading} style={{ ...S.btn,width:"100%",padding:"12px",background:"rgba(56,189,248,0.1)",color:"#38bdf8",border:"1px solid rgba(56,189,248,0.3)",fontSize:"14px" }}>{pdfLoading?"Generating...":"Download PDF Report"}</button>
            </div>
            <div style={S.card}>
              <div style={S.cardTitle}>Share</div>
              <button onClick={shareWhatsApp} disabled={pdfLoading} style={{ ...S.btn,width:"100%",padding:"11px",background:"rgba(37,211,102,0.1)",color:"#25d366",border:"1px solid rgba(37,211,102,0.3)",fontSize:"14px",marginBottom:"10px" }}>📱 WhatsApp</button>
              <input style={S.input} placeholder="Recipient email" value={emailData.to} onChange={e=>setEmailData(d=>({...d,to:e.target.value}))}/>
              <input style={S.input} placeholder="Your Gmail" value={emailData.from} onChange={e=>setEmailData(d=>({...d,from:e.target.value}))}/>
              <input style={S.input} type="password" placeholder="Gmail App Password" value={emailData.pass} onChange={e=>setEmailData(d=>({...d,pass:e.target.value}))}/>
              <button onClick={sendEmail} style={{ ...S.btn,width:"100%",padding:"10px",background:"rgba(0,255,157,0.1)",color:"#00ff9d",border:"1px solid rgba(0,255,157,0.3)" }}>Send Email</button>
              {emailStatus&&<p style={{ marginTop:"8px",fontSize:"12px",color:emailStatus.includes("✅")?"#00ff9d":"#f87171",textAlign:"center" }}>{emailStatus}</p>}
            </div>
          </div>
          <ShareReportPanel camState={camState} consultations={consultations} snapshots={snapshots}/>
        </>
      )}
    </div>
  );
}