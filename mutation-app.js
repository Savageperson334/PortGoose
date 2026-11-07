"use strict";
(() => {
  const OWNER = "Savageperson334";
  const segment = window.location.pathname.split("/").filter(Boolean)[0];
  const onPages = window.location.hostname.toLowerCase() === OWNER.toLowerCase() + ".github.io";
  const REPO = onPages && segment && segment !== "index.html" ? segment : "PortGoose";
  const BASE = "https://api.github.com/repos/" + OWNER + "/" + encodeURIComponent(REPO);
  const BRANCH = "main";
  const $ = id => document.getElementById(id);

  const TYPES = [
    {type:"grow", title:"Grow", symbol:"↗", desc:"Extend every living tip", tone:"#8af2c3"},
    {type:"fork", title:"Fork", symbol:"⑂", desc:"Split tips into new branches", tone:"#8ec8ff"},
    {type:"twist", title:"Twist", symbol:"⟳", desc:"Rotate geometry along its height", tone:"#c8b3ff"},
    {type:"mirror", title:"Mirror", symbol:"◈", desc:"Reflect and duplicate the structure", tone:"#ffc69e"},
    {type:"ripple", title:"Ripple", symbol:"≈", desc:"Bend the structure through a wave", tone:"#9eebff"},
    {type:"bloom", title:"Bloom", symbol:"✿", desc:"Grow blossoms at active tips", tone:"#ffa9d0"},
    {type:"prune", title:"Prune", symbol:"⌁", desc:"Remove a selection of branches", tone:"#d3e986"},
    {type:"thicken", title:"Thicken", symbol:"▰", desc:"Give branches more weight", tone:"#f8d982"},
  ];
  const byType = Object.fromEntries(TYPES.map(op => [op.type,op]));
  const state = {input:null,output:null,pending:null,saving:false,refreshing:false,pollHandle:null,history:[]};
  const tokenInput = $("token");

  function setStatus(message, error=false) {
    const el = $("status");
    el.textContent = message;
    el.classList.toggle("error", error);
  }
  function from64(value) {
    const binary = atob(value.replace(/\s/g,""));
    return new TextDecoder().decode(Uint8Array.from(binary, c => c.charCodeAt(0)));
  }
  function to64(text) {
    const bytes = new TextEncoder().encode(text);
    let binary="";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary);
  }
  async function github(path, token, settings={}) {
    const headers = {"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"};
    if (token) headers.Authorization = "Bearer " + token;
    if (settings.body) headers["Content-Type"] = "application/json";
    const response = await fetch(BASE + path, {
      method:settings.method || "GET", headers,
      body:settings.body ? JSON.stringify(settings.body) : undefined,
      cache:"no-store"
    });
    if (!response.ok) {
      let detail="";
      try { detail=(await response.json()).message || ""; } catch (_) {}
      const err = new Error("GitHub " + response.status + (detail ? ": " + detail : ""));
      err.status=response.status;
      throw err;
    }
    return response.json();
  }
  async function getJson(name, auth="") {
    const file=await github("/contents/" + name + "?ref=" + BRANCH, auth);
    return {data:JSON.parse(from64(file.content)),sha:file.sha};
  }
  function id() {
    return window.crypto && crypto.randomUUID ? crypto.randomUUID()
      : String(Date.now()) + "-" + Math.random().toString(36).slice(2);
  }
  function copy(data) {return JSON.parse(JSON.stringify(data));}
  function buttonsBusy(value) {
    document.querySelectorAll("button[data-action]").forEach(b => b.disabled=value);
    $("mutate-random").disabled=value;
    $("reset").disabled=value;
    $("reseed").disabled=value;
    $("reload").disabled=value;
  }

  function create(type, cls, text) {
    const node=document.createElement(type);
    if (cls) node.className=cls;
    if (text !== undefined) node.textContent=text;
    return node;
  }

  function showLibrary() {
    const grid=$("library");grid.replaceChildren();
    for (const op of TYPES) {
      const btn=create("button","library-op");
      btn.type="button";btn.dataset.action="add";btn.dataset.type=op.type;
      btn.style.setProperty("--tone",op.tone);
      btn.append(create("span","op-symbol",op.symbol));
      const content=create("span","op-copy");
      content.append(create("strong","",op.title),create("small","",op.desc));
      btn.append(content,create("span","add-symbol","+"));
      grid.append(btn);
    }
  }

  function renderStack() {
    const list=$("stack");list.replaceChildren();
    const ops=state.input?.operations || [];
    $("stack-count").textContent = ops.length + " / 18";
    if (!ops.length) {
      list.append(create("p","stack-empty","No mutations yet. Add an operation to change the seed."));
      return;
    }
    ops.forEach((op,i) => {
      const info=byType[op.type];
      if (!info) return;
      const item=create("div","stack-op" + (op.enabled ? "" : " inactive"));
      item.style.setProperty("--tone",info.tone);
      const number=create("div","stack-index",String(i+1).padStart(2,"0"));
      const text=create("div","stack-title");
      text.append(create("strong","",info.title),create("span","",info.desc));
      const controls=create("div","stack-tools");
      const actions=[
        ["toggle",op.enabled ? "Disable" : "Enable",op.enabled ? "◎" : "◉"],
        ["up","Move up","↑"],["down","Move down","↓"],["remove","Remove","×"]
      ];
      for (const [action,title,glyph] of actions) {
        const b=create("button","tiny-btn",glyph);
        b.type="button";b.dataset.action=action;b.dataset.id=op.id;
        b.title=title;b.setAttribute("aria-label",title + " " + info.title);
        if ((action==="up" && i===0)||(action==="down" && i===ops.length-1)) b.disabled=true;
        controls.append(b);
      }
      item.append(number,text,controls);
      list.append(item);
    });
  }

  function svg(name, attrs={}) {
    const node=document.createElementNS("http://www.w3.org/2000/svg",name);
    for (const [k,v] of Object.entries(attrs)) node.setAttribute(k,String(v));
    return node;
  }
  function drawCreature(output) {
    const art=$("creature");
    art.replaceChildren();
    const W=880,H=520;
    const bg=svg("g");
    for(let i=0;i<12;i++) {
      const x=55+i*70;
      bg.append(svg("line",{x1:x,x2:x,y1:22,y2:H-22,class:"grid-line"}));
    }
    for(let i=0;i<7;i++) {
      const y=38+i*74;
      bg.append(svg("line",{x1:25,x2:W-25,y1:y,y2:y,class:"grid-line"}));
    }
    bg.append(svg("circle",{cx:W/2,cy:H/2,r:190,class:"orbit-ring"}));
    bg.append(svg("circle",{cx:W/2,cy:H/2,r:120,class:"orbit-ring"}));
    art.append(bg);
    if (!output || !Array.isArray(output.segments)) return;
    const bounds=output.bounds;
    const x0=Math.min(Number(bounds.xmin),-.5),x1=Math.max(Number(bounds.xmax),.5);
    const y0=Math.min(Number(bounds.ymin),-1.1),y1=Math.max(Number(bounds.ymax),.25);
    const spanX=Math.max(1.25,x1-x0),spanY=Math.max(1.5,y1-y0);
    const scale=Math.min((W-105)/spanX,(H-95)/spanY);
    const centerX=(x0+x1)/2,centerY=(y0+y1)/2;
    const project=xy => [
      W/2+(xy[0]-centerX)*scale,
      H/2-(xy[1]-centerY)*scale
    ];
    const group=svg("g",{class:"organism"});
    const maxGen=Math.max(1,...output.segments.map(s=>s.generation || 0));
    for (const s of output.segments) {
      const a=project(s.a),b=project(s.b);
      const gen=s.generation || 0;
      const width=Math.max(1.6,Math.min(15,s.width*scale*.52));
      const hue=152+Math.round(gen/maxGen*112);
      group.append(svg("line",{
        x1:a[0],y1:a[1],x2:b[0],y2:b[1],
        stroke:"hsla(" + hue + ", 92%, 75%, .85)",
        "stroke-width":width,"stroke-linecap":"round"
      }));
      if(s.tip) group.append(svg("circle",{
        cx:b[0],cy:b[1],r:Math.max(3,width*.85),fill:"#f2f7d3",
        class:"tip-node"
      }));
    }
    for (const [i,flower] of (output.blooms || []).entries()) {
      const p=project(flower.center);
      const r=Math.max(4,Math.min(22,flower.radius*scale*.86));
      const petals=Math.max(3,Math.min(10,flower.petals || 5));
      for(let j=0;j<petals;j++) {
        const ang=Math.PI*2*j/petals+i*.23;
        group.append(svg("ellipse",{
          cx:p[0]+Math.cos(ang)*r*.65,cy:p[1]+Math.sin(ang)*r*.65,
          rx:r*.58,ry:r*.34,
          fill:i%2?"#e9a8ff":"#f8acd7",opacity:".88",
          transform:"rotate(" + (ang*180/Math.PI) + " " +
            (p[0]+Math.cos(ang)*r*.65) + " " + (p[1]+Math.sin(ang)*r*.65) + ")"
        }));
      }
      group.append(svg("circle",{cx:p[0],cy:p[1],r:r*.32,fill:"#fff6ac"}));
    }
    art.append(group);
  }

  function drawOutput() {
    const out=state.output;
    if(!out || out.schema!==2){
      $("generation").textContent="—";
      $("segments").textContent="—";
      $("blooms").textContent="—";
      $("model-label").textContent="Preparing procedural model…";
      drawCreature(null);
      return;
    }
    drawCreature(out);
    $("generation").textContent=(out.operations || []).filter(x=>x.enabled).length;
    $("segments").textContent=out.stats.segments;
    $("blooms").textContent=out.stats.blooms;
    $("model-label").textContent="Seed " + out.seed + " · Revision " + String(out.revision).slice(0,12);
    const latest=state.input?.revision;
    const mismatch=!!latest && out.revision!==latest;
    $("sync-indicator").textContent=mismatch ? "Processing mutation…" : "Synced with GitHub";
    $("sync-indicator").classList.toggle("waiting",mismatch);
    if(mismatch && !state.saving) setStatus("Mutation committed. Python is regenerating the form…");
    else if(!state.saving) setStatus("Model rendered from Python. Add, disable, reorder or remove operations.");
  }

  async function refresh() {
    if(state.refreshing) return;
    state.refreshing=true;
    try {
      const viewingToken=tokenInput.value.trim();
      const [infile,outfile]=await Promise.all([getJson("sandbox-input.json",viewingToken),getJson("sandbox.json",viewingToken)]);
      state.input=infile.data;
      state.output=outfile.data;
      renderStack();
      drawOutput();
      if(state.pending && state.output.revision===state.pending) {
        state.pending=null;
        setStatus("Mutation applied. The new model is live.");
      }
      if(state.output.schema!==2) setStatus("Python hasn't finished generating the first model yet.");
      const archive=$("archive-entries");
      if(archive.childElementCount===0) refreshArchive().catch(() => {});
    }catch(err) {
      setStatus("Unable to refresh model: " + err.message,true);
    }finally{state.refreshing=false;}
  }

  async function refreshArchive() {
    const {data}=await getJson("log.json");
    const list=$("archive-entries");list.replaceChildren();
    for (const entry of data.slice().reverse().slice(0,25)) {
      const row=create("div","archive-row");
      const date=new Date(entry.created_at);
      row.append(create("time","",Number.isNaN(date.getTime())?"Unknown time":date.toLocaleString()),
                 create("p","",entry.message));
      list.append(row);
    }
    if(!data.length) list.append(create("p","archive-row","No previous entries"));
  }

  async function save(mutator,label) {
    const token=tokenInput.value.trim();
    if (!token) {
      tokenInput.focus();
      setStatus("Paste your PortGoose GitHub token above to save a mutation.",true);
      return;
    }
    if (state.saving) return;
    state.saving=true;
    buttonsBusy(true);
    setStatus("Committing " + label + " to GitHub…");
    try {
      let done=false;
      for (let attempt=0;attempt<3;attempt++) {
        const file=await getJson("sandbox-input.json",token);
        const next=copy(file.data);
        const changed=mutator(next);
        if(changed===false) {
          setStatus("Nothing to change.");
          done=true;break;
        }
        next.schema=2;
        next.revision=id();
        next.operations=next.operations.slice(0,18);
        if (next.operations.some(op=>!byType[op.type])) throw new Error("Unrecognized operation");
        try {
          await github("/contents/sandbox-input.json",token,{
            method:"PUT", body:{
              message:"mutation: " + label, branch:BRANCH,
              sha:file.sha, content:to64(JSON.stringify(next,null,2)+"\n")
            }
          });
          state.input=next;
          state.pending=next.revision;
          renderStack();
          $("sync-indicator").textContent="Waiting for Python…";
          $("sync-indicator").classList.add("waiting");
          setStatus(label + " committed. The Python Action will regenerate the model.");
          done=true;break;
        } catch(err) {
          if((err.status===409 || err.status===422)&&attempt<2) continue;
          throw err;
        }
      }
      if(!done)throw new Error("Could not commit after retries.");
    } catch(err) {
      setStatus("Mutation was not saved: " + err.message,true);
    }finally{
      state.saving=false;
      buttonsBusy(false);
    }
  }

  function add(type) {
    const info=byType[type];if(!info)return;
    save(data=>{
      if (data.operations.length>=18) {
        setStatus("Maximum of 18 operations. Disable or remove one first.",true);
        return false;
      }
      data.operations.push({id:id(),type,enabled:true});
    },"add " + info.title);
  }

  document.addEventListener("click",event=>{
    const button=event.target.closest("button[data-action]");
    if (!button || button.disabled)return;
    const action=button.dataset.action;
    if(action==="add"){add(button.dataset.type);return;}
    const key=button.dataset.id;
    const opname=byType[(state.input?.operations||[]).find(o=>o.id===key)?.type]?.title || "operation";
    save(data=>{
      const ops=data.operations;
      const at=ops.findIndex(op=>op.id===key);
      if(at<0)return false;
      if(action==="remove")ops.splice(at,1);
      if(action==="toggle")ops[at].enabled=!ops[at].enabled;
      if(action==="up" && at>0)[ops[at-1],ops[at]]=[ops[at],ops[at-1]];
      if(action==="down" && at<ops.length-1)[ops[at+1],ops[at]]=[ops[at],ops[at+1]];
    }, action + " " + opname);
  });

  $("mutate-random").addEventListener("click",()=>add(TYPES[Math.floor(Math.random()*TYPES.length)].type));
  $("reset").addEventListener("click",()=>save(data=>{data.operations=[];data.seed=4;},"reset mutation stack"));
  $("reseed").addEventListener("click",()=>save(data=>{
    let n=Math.floor(Math.random()*1000000);
    if(n===data.seed)n=(n+1)%1000000;
    data.seed=n;
  },"reseed organism"));
  $("reload").addEventListener("click",refresh);
  $("archive-refresh").addEventListener("click",()=>refreshArchive().catch(err=>setStatus(err.message,true)));
  $("repo-link").href="https://github.com/"+OWNER+"/"+REPO;
  $("input-link").href="https://github.com/"+OWNER+"/"+REPO+"/blob/main/sandbox-input.json";
  $("output-link").href="https://github.com/"+OWNER+"/"+REPO+"/blob/main/sandbox.json";
  $("actions-link").href="https://github.com/"+OWNER+"/"+REPO+"/actions/workflows/python-sandbox.yml";
  showLibrary();
  refresh();
  // Public (unauthenticated) API requests are limited to ~60 per hour.
  // Poll quickly ONLY while an authenticated mutation is awaiting processing;
  // refresh public viewers at a much slower cadence to preserve that budget.
  window.setInterval(() => {if(state.pending && tokenInput.value.trim()) refresh();},10000);
  window.setInterval(() => {if(!state.pending) refresh();},180000);
})();