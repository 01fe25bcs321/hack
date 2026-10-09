const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const el=id=>document.getElementById(id);
let latestComparison=null;
let selectedFile=null;
function shortHash(v){return v?String(v).slice(0,24)+'…':'Not available'}
async function loadTrustedDocuments(){
 const select=el('originalId');
 try{const r=await api.request('/api/documents');const docs=r.documents||[];
  select.innerHTML=docs.length?'<option value="">Select a trusted document</option>'+docs.map(d=>`<option value="${esc(d.document_id)}">${esc(d.title||d.document_id)} · ${esc(d.document_id)} · v${esc(d.version)}</option>`).join(''):'<option value="">No trusted signed documents found</option>';
 }catch(e){select.innerHTML='<option value="">Could not load documents</option>';}
}
el('originalId').addEventListener('change',async()=>{
 const id=el('originalId').value;const box=el('trustedSummary');if(!id){box.className='empty';box.textContent='Select a document to see its summary and hash.';return}
 try{const d=await api.request('/api/documents/'+encodeURIComponent(id));box.className='';box.innerHTML=`<div class="result-tile"><span>Trusted document</span><strong>${esc(d.title)} · ${esc(d.document_id)}</strong></div><p>${esc(d.summary||'No summary available.')}</p><p class="mono">SHA-256 · ${esc(d.document_hash)}</p><p class="muted">${esc(d.source_count||0)} source(s) · Version ${esc(d.version)}</p>`}catch(e){box.className='empty';box.textContent=e.message}
});
el('compareBtn').onclick=async()=>{
 const file=el('compareDocument').files[0],id=el('originalId').value;
 const result=el('verifyResult'),review=el('changeReview');result.classList.remove('hidden');review.classList.add('hidden');latestComparison=null;selectedFile=file;
 if(!id||!file){result.innerHTML='<div class="verify-status danger">Choose both documents</div><p>Select a trusted document and a candidate JSON file before verifying.</p>';return}
 const fd=new FormData();fd.append('original_document_id',id);fd.append('document',file);
 el('compareBtn').disabled=true;el('compareBtn').textContent='Checking document…';
 try{const r=await api.request('/api/verify/compare',{method:'POST',body:fd});latestComparison=r;
  const sig=r.signature_check||{};const trustedSig=r.trusted_signature_check||{};
  result.innerHTML=`<div class="verify-status ${r.valid?'success':'danger'}">${r.valid?'Nothing was tampered with':'Verification needs review'}</div><p>${esc(r.message)}</p><div class="verification-result-grid"><div class="result-tile"><span>Content comparison</span><strong>${r.content_matches?'Exact content match':'Differences found'}</strong></div><div class="result-tile"><span>SHA-256 integrity</span><strong class="${sig.hash_valid?'success':'danger'}">${sig.hash_valid?'Valid':'Failed / missing'}</strong></div><div class="result-tile"><span>Ed25519 signature</span><strong class="${sig.signature_valid?'success':'danger'}">${sig.signature_valid?'Valid':'Invalid / missing'}</strong></div><div class="result-tile"><span>Trusted document</span><strong>${esc(r.trusted_title)} · ${esc(r.document_id)}</strong></div><div class="result-tile"><span>Candidate file</span><strong>${esc(r.candidate_file)}</strong></div><div class="result-tile"><span>Summary comparison</span><strong class="${r.summary_matches?'success':'danger'}">${r.summary_matches?'Summaries match':'Summaries differ'}</strong></div><div class="result-tile"><span>Candidate hash</span><strong class="mono">${esc(shortHash(r.candidate_hash))}</strong></div><div class="result-tile"><span>Current document signature</span><strong class="${trustedSig.signature_valid?'success':'danger'}">${trustedSig.signature_valid?'Valid':'Invalid'}</strong></div><div class="result-tile"><span>Candidate document signature</span><strong class="${sig.signature_valid?'success':'danger'}">${sig.signature_valid?'Valid':'Invalid'}</strong></div><div class="result-tile"><span>Signature origin</span><strong class="${r.signer_matches?'success':'danger'}">${r.signer_matches?'Matches trusted signature':'Different signature origin'}</strong></div></div><div class="summary-compare"><div><h3>Current document summary</h3><p>${esc(r.trusted_summary||'No summary available.')}</p></div><div><h3>Candidate document summary</h3><p>${esc(r.candidate_summary||'No summary available.')}</p></div></div>${r.valid?'<div class="notice success">All checks passed. The file name does not affect verification; content and signature checks are valid.</div>':''}`;
  if(r.valid){review.classList.add('hidden');return}
  review.classList.remove('hidden');
  const changes=r.changes||[];
  const cards=changes.length?changes.map((c,i)=>`<article class="change-card"><p class="eyebrow">DIFFERENCE ${i+1} OF ${changes.length}</p><h3>${esc(c.section||'Document field')}</h3><div class="change-grid"><div><b>Candidate file</b><span>${esc(c.file||r.candidate_file)}</span></div><div><b>JSON field path</b><span class="mono">${esc(c.field_path||c.line||'Not available')}</span></div><div><b>Location</b><span>${esc(c.page||'JSON document field; page unavailable')}</span></div><div><b>Previous trusted value</b><span class="diff-value">${esc(JSON.stringify(c.previous,null,2))}</span></div><div><b>Candidate value</b><span class="diff-value">${esc(JSON.stringify(c.current,null,2))}</span></div></div></article>`).join(''):'<div class="notice danger">No content fields differed, but the candidate hash or signature did not validate. Check the cryptographic details above.</div>';
  review.innerHTML=`<p class="eyebrow">DETAILED CHANGE REPORT</p><h2>${changes.length} difference${changes.length===1?'':'s'} detected</h2><p class="muted">The browser does not expose the candidate file’s full local folder path. The report identifies the uploaded filename and exact JSON field path; original source filenames are shown below where available.</p>${r.source_files?.length?`<div class="result-tile"><span>Sources attached to trusted document</span><strong>${r.source_files.map(esc).join(' · ')}</strong></div>`:''}${cards}<div class="change-summary"><span><strong>Decision required.</strong> Accepting will create a newly signed trusted version and delete the superseded trusted document and its generated files. Declining leaves the current trusted document unchanged and records the declined review.</span></div><div class="decision-bar"><p>Review the differences above before deciding.</p><div class="actions"><button id="declineAllBtn" class="button decline" type="button">Decline candidate</button><button id="acceptAllBtn" class="button approve" type="button">Accept &amp; make current</button></div></div>`;
  el('acceptAllBtn').onclick=()=>submitDecision('accept');el('declineAllBtn').onclick=()=>submitDecision('decline');
 }catch(e){result.innerHTML=`<div class="verify-status danger">Could not verify document</div><p>${esc(e.message)}</p><p class="muted">Confirm the selected file is a DocFusion JSON document and try again.</p>`}
 finally{el('compareBtn').disabled=false;el('compareBtn').textContent='Verify & compare'}
};
async function submitDecision(decision){
 if(!latestComparison||!selectedFile)return;
 const review=el('changeReview');review.insertAdjacentHTML('afterbegin',`<div class="notice">${decision==='accept'?'Accepting and signing candidate…':'Recording decline…'}</div>`);
 const fd=new FormData();fd.append('original_document_id',latestComparison.document_id);fd.append('decision',decision);fd.append('document',selectedFile);
 try{const r=await api.request('/api/verify/decision',{method:'POST',body:fd});
  review.innerHTML=`<div class="notice ${decision==='accept'?'success':'danger'}"><strong>${decision==='accept'?'Candidate accepted':'Candidate declined'}</strong><p>${esc(r.message)}</p>${decision==='accept'?`<p>Current document: <strong>${esc(r.document_id)}</strong></p><p class="mono">New SHA-256: ${esc(r.document_hash)}</p><a class="button" href="/static/document.html?id=${encodeURIComponent(r.document_id)}">Open current document</a>`:`<p>Declined reviews recorded: ${esc(r.declined_count)}</p><p>Current trusted document remains: ${esc(r.document_id)}</p>`}</div>`;
  if(decision==='accept')await loadTrustedDocuments();
 }catch(e){review.insertAdjacentHTML('afterbegin',`<div class="notice danger">Decision failed: ${esc(e.message)}</div>`)}
}
loadTrustedDocuments();
