let analysis = null;
let sourceCache = [];
let activeSection = 'summary';
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
const el = id => document.getElementById(id);
const msg = el('message'), analyzeBtn = el('analyzeBtn'), generateBtn = el('generateBtn');
const providerInputs = [...document.querySelectorAll('input[name="aiProvider"]')];
let providerInfo = null;
const sections = [
  {id:'summary', label:'Summary', icon:'▤'},
  {id:'predictions', label:'AI Prediction', icon:'✧'},
  {id:'analysis', label:'AI Analysis', icon:'◈'},
  {id:'conflicts', label:'Conflicts', icon:'⇄'},
  {id:'duplicates', label:'Duplicates', icon:'▣'},
  {id:'alerts', label:'Alerts', icon:'⚑'},
  {id:'entities', label:'Entities', icon:'◎'},
  {id:'citations', label:'Sources & Citations', icon:'↗'},
  {id:'provenance', label:'Provenance', icon:'⌘'},
  {id:'quality', label:'Quality Report', icon:'✓'}
];
function provider(){ return document.querySelector('input[name="aiProvider"]:checked').value; }
function safeList(items, emptyText){ return items?.length ? items : []; }
function empty(text){ return `<div class="analysis-empty"><span class="empty-symbol">i</span><div><strong>Nothing to show yet</strong><p>${esc(text)}</p></div></div>`; }
function card(title, body, meta='') { return `<article class="analysis-card">${meta ? `<div class="analysis-meta">${esc(meta)}</div>` : ''}<h3>${esc(title)}</h3><div class="analysis-card-body">${body}</div></article>`; }
function sourceName(id){ const source=sourceCache.find(s=>s.source_id===id); return source ? source.name : id; }
function renderSources(s){ sourceCache=s; const box=el('sourceRegistry'); box.innerHTML=s.length?s.map(x=>`<div class="source-row"><div><strong>${esc(x.name)}</strong><span class="meta">${esc(x.source_id)} · ${esc(x.source_type)} · ${esc(x.metadata?.classification||'INTERNAL')} · ${esc(x.processing_status)}</span></div><div class="hash">${esc(x.content_hash)}</div><button class="button secondary danger delete-source" data-id="${esc(x.source_id)}">Delete</button></div>`).join(''):'<div class="empty">No sources ingested yet.</div>'; box.querySelectorAll('.delete-source').forEach(b=>b.onclick=async()=>{try{await api.request(`/api/sources/${encodeURIComponent(b.dataset.id)}`,{method:'DELETE'}); analysis=null;generateBtn.disabled=true;el('result').classList.add('hidden');await refresh()}catch(e){msg.textContent=e.message}}); }
async function refresh(){ const sources=await api.sources(); analyzeBtn.disabled=!sources.length; renderSources(sources); msg.textContent=sources.length?`${sources.length} source(s) ready for analysis.`:'Add at least one source before analysis.'; }
async function loadProviders(){try{providerInfo=await api.providers();el('geminiStatus').textContent=providerInfo.gemini.configured?`Ready · ${providerInfo.gemini.model}`:'API key not configured';const models=providerInfo.ollama.models||[];el('ollamaModel').innerHTML=models.length?models.map(m=>`<option>${esc(m)}</option>`).join(''):'<option value="">No local models detected</option>';el('ollamaStatus').textContent=providerInfo.ollama.status==='connected'?`Online · ${models.length} model(s)`:`Offline · ${providerInfo.ollama.base_url}`}catch(e){el('geminiStatus').textContent='Provider status unavailable';}}
function renderOverview(a,mode){
  el('result').classList.remove('hidden');
  el('result').innerHTML=`<div class="analysis-workspace"><div class="analysis-heading"><div><p class="eyebrow">ANALYSIS WORKSPACE</p><h2>Evidence intelligence report</h2><p class="muted">${esc(mode)} · Select a section to inspect its results. The signed document is generated separately.</p></div><span class="analysis-status"><i></i> Analysis complete</span></div><div class="analysis-kpis"><div><span>Claims</span><strong>${a.claims?.length||0}</strong></div><div><span>Conflicts</span><strong>${a.conflicts?.length||0}</strong></div><div><span>Duplicates</span><strong>${a.duplicates?.length||0}</strong></div><div><span>Entities</span><strong>${a.entities?.length||0}</strong></div><div><span>Predictions</span><strong>${a.predictions?.length||0}</strong></div><div><span>Sources</span><strong>${sourceCache.length}</strong></div></div><div class="analysis-layout"><nav class="analysis-nav" aria-label="Analysis sections">${sections.map(s=>`<button type="button" class="analysis-tab ${s.id===activeSection?'active':''}" data-section="${s.id}"><span>${s.icon}</span>${s.label}<b>›</b></button>`).join('')}</nav><section class="analysis-panel" id="analysisPanel" aria-live="polite"></section></div></div>`;
  el('result').querySelectorAll('.analysis-tab').forEach(button=>button.addEventListener('click',()=>showSection(button.dataset.section)));
  showSection(activeSection);
}
function showSection(id){
  activeSection=id;
  el('result').querySelectorAll('.analysis-tab').forEach(b=>b.classList.toggle('active',b.dataset.section===id));
  const panel=el('analysisPanel'); if(!panel||!analysis)return;
  const a=analysis; let html='';
  if(id==='summary'){
    html=`<p class="eyebrow">EXECUTIVE BRIEF</p><h2>Summary</h2><p class="analysis-lead">${esc(a.summary||'The AI did not return an executive summary for this run.')}</p>`;
    if(a.key_points?.length)html+=`<h3>Key findings</h3><ul class="analysis-bullet-list">${a.key_points.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
    html+=`<div class="analysis-callout"><strong>Review before signing</strong><p>${a.conflicts?.length?`${a.conflicts.length} conflict(s) require attention.`:'No conflicts were returned by the analysis.'} ${a.missing_information?.length?`${a.missing_information.length} information gap(s) were identified.`:''}</p></div>`;
  } else if(id==='predictions'){
    html=`<p class="eyebrow">FORWARD-LOOKING INSIGHTS</p><h2>AI Prediction</h2><p class="muted">Predictions are estimates based on source evidence, not verified facts.</p>`;
    html+=(a.predictions||[]).map(p=>card(p.prediction,`<p><b>Basis</b></p><ul>${(p.basis||[]).map(x=>`<li>${esc(x)}</li>`).join('')||'<li>No basis provided.</li>'}</ul><p><b>Confidence:</b> ${esc(p.confidence||'Not provided')}</p>${p.caveats?.length?`<p><b>Caveats</b></p><ul>${p.caveats.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}`,'AI-generated estimate')).join('')||empty('The AI returned no evidence-supported predictions. This is preferable to inventing predictions without enough evidence.');
  } else if(id==='analysis'){
    html=`<p class="eyebrow">CLAIMS & INTERPRETATION</p><h2>AI Analysis</h2>`;
    if(a.ai_assessment)html+=card('AI assessment',`<p>${esc(a.ai_assessment)}</p>`,'Overall interpretation');
    html+=(a.claims||[]).map(c=>card(c.claim,`<p><b>Classification:</b> ${esc(c.classification)} &nbsp; <b>Confidence:</b> ${Math.round((Number(c.confidence)||0)*100)}%</p><p><b>Sources:</b> ${esc((c.sources||[]).map(sourceName).join(', ')||'No source linked')}</p>${c.evidence?.length?`<p><b>Evidence</b></p><ul>${c.evidence.map(e=>`<li>${esc(e)}</li>`).join('')}</ul>`:''}`,c.claim_type||'Claim')).join('');
    if(!a.claims?.length&&!a.ai_assessment)html+=empty('No detailed claims or assessment were returned.');
  } else if(id==='conflicts'){
    html=`<p class="eyebrow">CONTRADICTION REVIEW</p><h2>Conflicts</h2><p class="muted">Conflicting facts are preserved for review and should not be silently resolved.</p>`;
    html+=(a.conflicts||[]).map(c=>card(c.field,`<div class="conflict-values">${(c.values||[]).map(v=>`<div><span>${esc(sourceName(v.source))}</span><strong>${esc(v.value)}</strong></div>`).join('')}</div><p><b>Status:</b> ${esc(c.status||'UNRESOLVED')}</p><p>${esc(c.reason||'No resolution rationale supplied.')}</p>`,c.classification||'Conflict')).join('')||empty('No conflicts detected in this analysis.');
  } else if(id==='duplicates'){
    html=`<p class="eyebrow">DEDUPLICATION</p><h2>Duplicates</h2>`;
    html+=(a.duplicates||[]).map(d=>card((d.claims||[]).join(' / '),`<p>${esc(d.reason||'Similar or repeated information detected.')}</p><p><b>Sources:</b> ${esc((d.sources||[]).map(sourceName).join(', ')||'Source references unavailable')}</p>`,d.classification||'Duplicate')).join('')||empty('No duplicate claims were detected.');
  } else if(id==='alerts'){
    const alerts=[];
    (a.conflicts||[]).filter(c=>(c.status||'').toUpperCase().includes('UNRESOLVED')).forEach(c=>alerts.push({level:'Review',title:`Unresolved conflict: ${c.field}`,detail:(c.values||[]).map(v=>`${sourceName(v.source)}: ${v.value}`).join(' · ')}));
    (a.claims||[]).filter(c=>['UNSUPPORTED','UNCERTAIN'].includes((c.classification||'').toUpperCase())).forEach(c=>alerts.push({level:'Evidence gap',title:c.claim,detail:`Classification: ${c.classification}. Sources: ${(c.sources||[]).map(sourceName).join(', ')||'none linked'}`}));
    (a.missing_information||[]).forEach(item=>alerts.push({level:'Missing information',title:item,detail:'The analysis indicates this information was not available or needs clarification.'}));
    html=`<p class="eyebrow">REQUIRES ATTENTION</p><h2>Alerts</h2>`;
    html+=alerts.map(a=>card(a.title,`<p>${esc(a.detail)}</p>`,a.level)).join('')||empty('No unresolved conflicts, unsupported claims or missing-information alerts were returned.');
  } else if(id==='entities'){
    html=`<p class="eyebrow">ENTITY RESOLUTION</p><h2>Entities</h2>`;
    html+=(a.entities||[]).map(e=>card(e.value,`<p><b>Type:</b> ${esc(e.type)}</p><p><b>Found in:</b> ${esc((e.sources||[]).map(sourceName).join(', ')||'No source linked')}</p>`,'Identified entity')).join('')||empty('No entities were identified.');
    if(a.important_dates?.length)html+=`<h3>Important dates</h3>`+a.important_dates.map(d=>card(d.value,`<p>${esc(d.context)}</p><p><b>Sources:</b> ${esc((d.sources||[]).map(sourceName).join(', '))}</p>`,'Date')) .join('');
    if(a.important_numbers?.length)html+=`<h3>Important numbers</h3>`+a.important_numbers.map(n=>card(n.value,`<p>${esc(n.context)}</p><p><b>Sources:</b> ${esc((n.sources||[]).map(sourceName).join(', '))}</p>`,'Number')).join('');
  } else if(id==='citations'){
    html=`<p class="eyebrow">SOURCE EVIDENCE</p><h2>Sources & Citations</h2>`;
    html+=(a.source_evidence||[]).map(e=>card(e.claim||'Claim evidence',`<p><b>Source:</b> ${esc(sourceName(e.source_id))}</p><blockquote>${esc(e.evidence||'No evidence excerpt returned.')}</blockquote><p><b>Confidence:</b> ${esc(e.confidence||'Not provided')}</p>`,e.source_id||'Evidence')).join('');
    if(!a.source_evidence?.length){html+=(a.claims||[]).map(c=>card(c.claim,`<p><b>Sources:</b> ${esc((c.sources||[]).map(sourceName).join(', ')||'No source linked')}</p>${c.evidence?.map(e=>`<blockquote>${esc(e)}</blockquote>`).join('')||'<p>No evidence excerpts returned.</p>'}`, 'Claim citation')).join('');}
    if(!a.source_evidence?.length&&!a.claims?.length)html+=empty('No claim-level citations were returned.');
  } else if(id==='provenance'){
    html=`<p class="eyebrow">TRACEABILITY</p><h2>Provenance</h2><p class="muted">Trace claims to their source files. The signed document will preserve source hashes and provenance records.</p>`;
    html+=(a.claims||[]).map(c=>card(c.claim,`<p><b>Source chain</b></p><ol>${(c.sources||[]).map(s=>`<li>${esc(sourceName(s))} <span class="muted">(${esc(s)})</span></li>`).join('')||'<li>No source link supplied.</li>'}</ol>${c.evidence?.length?`<p><b>Evidence</b></p>${c.evidence.map(e=>`<blockquote>${esc(e)}</blockquote>`).join('')}`:''}`, 'Claim → source')).join('')||empty('No claims are available to trace.');
  } else if(id==='quality'){
    const claims=a.claims||[]; const cited=claims.filter(c=>c.sources?.length).length; const unsupported=claims.filter(c=>['UNSUPPORTED','UNCERTAIN'].includes((c.classification||'').toUpperCase())).length; const citationPct=claims.length?Math.round(cited/claims.length*100):0; const unsupportedPct=claims.length?Math.round(unsupported/claims.length*100):0; const completeSources=new Set(claims.flatMap(c=>c.sources||[])).size; const provenancePct=claims.length?Math.round(claims.filter(c=>c.sources?.length&&c.evidence?.length).length/claims.length*100):0;
    html=`<p class="eyebrow">QUALITY & TRUST</p><h2>Quality Report</h2><div class="quality-grid"><div><span>Claims with source links</span><strong>${citationPct}%</strong><small>${cited} of ${claims.length} claims</small></div><div><span>Claims needing evidence review</span><strong>${unsupportedPct}%</strong><small>${unsupported} claims</small></div><div><span>Claim evidence completeness</span><strong>${provenancePct}%</strong><small>Claims with both source and evidence</small></div><div><span>Sources referenced by claims</span><strong>${completeSources}/${sourceCache.length}</strong><small>Distinct sources linked to claims</small></div></div><p class="muted quality-note">These metrics describe this analysis response, not a benchmarked accuracy score. Extraction/OCR success and cryptographic verification are measured separately by their own workflows.</p>`;
    if(a.missing_information?.length)html+=`<h3>Known information gaps</h3><ul class="analysis-bullet-list">${a.missing_information.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
  }
  panel.innerHTML=html;
}
providerInputs.forEach(input=>input.onchange=()=>{el('ollamaModel').disabled=provider()!=='ollama'});
function setUploadProgress(active, files=[]){const box=el('uploadProgress');if(!box)return;box.classList.toggle('hidden',!active);if(!active)return;el('uploadProgressTitle').textContent=files.length===1?'Uploading 1 file':'Uploading '+files.length+' files';el('uploadProgressText').textContent='Securely uploading files, extracting content and calculating source hashes. Large files may take a little longer.';el('uploadProgressFiles').innerHTML=files.map(file=>`<div class="upload-progress-file"><span class="upload-file-icon">${esc((file.name.split('.').pop()||'FILE').toUpperCase())}</span><span class="upload-file-name">${esc(file.name)}</span><span class="upload-file-size">${(file.size/1024/1024).toFixed(2)} MB</span><span class="upload-file-pulse" aria-label="Processing"></span></div>`).join('');box.scrollIntoView({behavior:'smooth',block:'nearest'});}
const fileInput=el('files');const dropZone=fileInput?.closest('.drop');
if(fileInput&&dropZone){fileInput.addEventListener('change',()=>{dropZone.classList.toggle('has-files',fileInput.files.length>0);const strong=dropZone.querySelector('strong');if(strong)strong.textContent=fileInput.files.length?`${fileInput.files.length} file${fileInput.files.length===1?'':'s'} selected`:'PDF · DOCX · TXT · CSV · JSON';});['dragenter','dragover'].forEach(name=>dropZone.addEventListener(name,event=>{event.preventDefault();dropZone.classList.add('drag-over')}));['dragleave','drop'].forEach(name=>dropZone.addEventListener(name,event=>{event.preventDefault();dropZone.classList.remove('drag-over')}));dropZone.addEventListener('drop',event=>{if(event.dataTransfer?.files?.length){try{fileInput.files=event.dataTransfer.files;fileInput.dispatchEvent(new Event('change',{bubbles:true}))}catch(_){}}});}
el('uploadForm').onsubmit=async event=>{event.preventDefault();const files=[...(el('files').files||[])];try{if(!files.length)throw new Error('Choose at least one file.');const fd=new FormData();for(const file of files)fd.append('files',file);fd.append('classification',el('sourceClassification').value);const submit=el('uploadForm').querySelector('button[type="submit"]');submit.disabled=true;submit.dataset.originalText=submit.textContent;submit.textContent='Uploading…';setUploadProgress(true,files);msg.textContent='Please keep this page open while your files are processed.';await api.request('/api/sources/upload',{method:'POST',body:fd});el('files').value='';dropZone?.classList.remove('has-files');if(dropZone?.querySelector('strong'))dropZone.querySelector('strong').textContent='PDF · DOCX · TXT · CSV · JSON';analysis=null;generateBtn.disabled=true;setUploadProgress(false);msg.textContent=`Successfully uploaded and processed ${files.length} file${files.length===1?'':'s'}.`;await refresh()}catch(error){setUploadProgress(false);msg.textContent=error.message}finally{const submit=el('uploadForm').querySelector('button[type="submit"]');submit.disabled=false;submit.textContent=submit.dataset.originalText||'Ingest files'}};
el('urlForm').onsubmit=async event=>{event.preventDefault();try{await api.request('/api/sources/url',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:el('url').value,classification:el('sourceClassification').value})});analysis=null;generateBtn.disabled=true;await refresh()}catch(error){msg.textContent=error.message}};
el('textForm').onsubmit=async event=>{event.preventDefault();try{await api.request('/api/sources/text',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:el('textName').value,content:el('textContent').value,classification:el('sourceClassification').value})});analysis=null;generateBtn.disabled=true;await refresh()}catch(error){msg.textContent=error.message}};
el('analyzeBtn').onclick=async()=>{const selectedProvider=provider();const model=selectedProvider==='ollama'?el('ollamaModel').value:null;analyzeBtn.disabled=true;generateBtn.disabled=true;msg.textContent='Analyzing sources and preparing evidence-backed results…';activeSection='summary';try{analysis=await api.analyze(selectedProvider,model);renderOverview(analysis,selectedProvider==='ollama'?'Private AI · Ollama':'Public AI · Gemini');generateBtn.disabled=false;msg.textContent='Analysis complete. Open any section to inspect its results, then generate the signed document.';el('result').scrollIntoView({behavior:'smooth',block:'start'})}catch(error){analysis=null;el('result').classList.add('hidden');msg.textContent=error.message}finally{analyzeBtn.disabled=false}};
el('generateBtn').onclick=async()=>{if(!analysis)return;generateBtn.disabled=true;try{const doc=await api.generate(analysis,'DocFusion AI Report',el('outputClassification').value);msg.innerHTML=`Signed document <strong>${esc(doc.document_id)}</strong> created. <a href="/static/document.html?id=${encodeURIComponent(doc.document_id)}">Open document</a>`}catch(error){msg.textContent=error.message}finally{generateBtn.disabled=false}};
loadProviders();refresh().catch(error=>{msg.textContent=error.message});
