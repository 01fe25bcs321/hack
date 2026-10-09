const API_BASE = window.DOCFUSION_API_URL || '';
const api = {
  async request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const r = await fetch(`${API_BASE}${path}`, {...options, headers});
    const data = await r.json().catch(() => ({detail: r.statusText}));
    if (!r.ok) throw new Error(data.detail || 'Request failed');
    return data;
  },
  sources(){return this.request('/api/sources')},
  providers(){return this.request('/api/ai/providers')},
  analyze(provider, model){const q=new URLSearchParams({provider}); if(model)q.set('model',model); return this.request('/api/analyze?'+q,{method:'POST'})},
  generate(analysis,title='DocFusion AI Report',output_classification='INTERNAL'){return this.request('/api/documents/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({analysis,title,output_classification})})}
};
