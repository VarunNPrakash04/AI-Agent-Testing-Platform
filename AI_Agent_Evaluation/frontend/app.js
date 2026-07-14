/* ═══════════════════════════════════════════════
   Benchmark Studio — app.js
   Full logic: CRUD, evaluation, results
   ═══════════════════════════════════════════════ */
'use strict';

/* ─── STATE ─── */
const S = {
  datasets:        [],
  results:         [],
  activity:        [],
  selDataset:      null,
  selFramework:    'deepeval',
  selMetrics:      [],
  editId:          null,
  deleteId:        null,
  resultViewId:    null,
  isEditing:       false,
  filterQ:         '',
  currentPage:     'overview',
};

let _file = null;

/* ─── METRICS CATALOG ─── */
const METRICS = {
  deepeval: [
    { id:'answer_relevancy',     name:'Answer Relevancy',           cat:'rag',     desc:'Measures how relevant the generated answer is to the input question.' },
    { id:'faithfulness',         name:'Faithfulness',               cat:'rag',     desc:'Checks if the answer is factually grounded in the provided context.' },
    { id:'contextual_precision', name:'Contextual Precision',       cat:'rag',     desc:'Evaluates whether each retrieved context node is relevant to the query.' },
    { id:'contextual_recall',    name:'Contextual Recall',          cat:'rag',     desc:'Measures how well the retrieved context covers the expected answer.' },
    { id:'contextual_relevancy', name:'Contextual Relevancy',       cat:'rag',     desc:'Assesses the overall relevance of all retrieved context to the query.' },
    { id:'hallucination',        name:'Hallucination',              cat:'quality', desc:'Detects factual inconsistencies between the answer and its context.' },
    { id:'bias',                 name:'Bias Detection',             cat:'safety',  desc:'Identifies unfair bias or prejudice in the generated response.' },
    { id:'toxicity',             name:'Toxicity',                   cat:'safety',  desc:'Detects harmful, offensive, or unsafe content in the output.' },
    { id:'summarization',        name:'Summarization Quality',      cat:'quality', desc:'Evaluates the quality of generated summaries against source documents.' },
    { id:'g_eval',               name:'G-Eval',                     cat:'quality', desc:'LLM-as-judge evaluation using custom task-specific criteria.' },
    { id:'ragas_compat',         name:'RAGAS Compatibility Score',  cat:'rag',     desc:'RAGAS-compatible scoring within the DeepEval framework.' },
    { id:'json_correctness',     name:'JSON Correctness',           cat:'quality', desc:'Validates if the output is a valid and structurally correct JSON.' },
  ],
  ragas: [
    { id:'faithfulness',            name:'Faithfulness',                cat:'rag',     desc:'Measures factual consistency of the answer against retrieved context.' },
    { id:'answer_relevancy',        name:'Answer Relevancy',            cat:'rag',     desc:'Assesses how pertinent the generated answer is to the user question.' },
    { id:'context_precision',       name:'Context Precision',           cat:'rag',     desc:'Evaluates signal-to-noise ratio in the retrieved context nodes.' },
    { id:'context_recall',          name:'Context Recall',              cat:'rag',     desc:'Measures if the ground truth answer can be inferred from context.' },
    { id:'context_entity_recall',   name:'Context Entity Recall',       cat:'rag',     desc:'Checks that key entities from ground truth are in retrieved context.' },
    { id:'noise_sensitivity',       name:'Noise Sensitivity',           cat:'quality', desc:'Tests robustness of the pipeline against irrelevant context passages.' },
    { id:'answer_similarity',       name:'Answer Semantic Similarity',  cat:'quality', desc:'Semantic similarity between generated and ground truth answers.' },
    { id:'answer_correctness',      name:'Answer Correctness',          cat:'quality', desc:'Combined factual and semantic accuracy of the generated answer.' },
  ],
  data_integrity: [
    { id:'file_exists',          name:'Destination File Exists',    cat:'quality', desc:'Validates that the file was successfully written to the destination.' },
    { id:'file_size',            name:'File Size > 0',              cat:'quality', desc:'Ensures the generated file is not empty.' },
    { id:'row_count',            name:'Row Count Match',            cat:'quality', desc:'Checks if the number of rows matches the expected dataset size.' },
    { id:'schema_valid',         name:'Schema Valid',               cat:'quality', desc:'Validates the column headers and data types against the schema.' },
  ],
  data_transformation: [
    { id:'exact_match',          name:'Exact Output Match',         cat:'quality', desc:'Checks if the canonical formula or output perfectly matches the ground truth.' },
    { id:'formula_equiv',        name:'Semantic Output Equivalence',cat:'quality', desc:'Checks if the output is logically/semantically equivalent.' },
    { id:'logic_check',          name:'Logic Validation Check',     cat:'quality', desc:'Validates business rules and constraints on the output.' },
  ],
};


/* ─── API HELPER ─── */
const API_BASE = '/api/v1';

async function fetchApi(endpoint, options = {}) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error((err.error && err.error.message) || `API Error: ${res.status}`);
    }
    if (res.status === 204) return null;
    return await res.json();
  } catch (error) {
    console.error(error);
    throw error;
  }
}

let S_agents = [];

async function bootstrapApp() {
  try {
    const [agents, overview] = await Promise.all([
      fetchApi('/agents'),
      fetchApi('/dashboard/overview')
    ]);
    S_agents = agents || [];
    S.datasets = (overview?.recent_runs || []).map((run, index) => ({
      id: run.run_id,
      name: `Run ${index + 1}`,
      tags: 'history',
      description: `Execution ${run.status}`,
      fileName: run.suite_id,
      fileSize: 0,
      questionCount: run.total_tests || 0,
      status: 'Ready',
      uploadedAt: run.started_at || new Date().toISOString(),
    }));
    refreshCounters();
    updateAgentDropdown();
    if (S.currentPage === 'overview') renderActivity();
  } catch (error) {
    console.error('Bootstrap failed', error);
  }
}

function updateAgentDropdown() {
    const runModelSelect = document.getElementById('runModel');
    if (runModelSelect) {
        if (S_agents && S_agents.length > 0) {
            runModelSelect.innerHTML = S_agents.map(a => `<option value="${a.id}">${esc(a.agent_name)}</option>`).join('');
        } else {
            runModelSelect.innerHTML = '<option value="" disabled selected>No pipelines/agents registered (Register in Pipelines tab)</option>';
        }
        // Force update the run summary to reflect the change
        refreshSummary();
    }
}

/* ─── NAV ─── */
function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(n => n.classList.remove('active'));

  const pg = document.getElementById('page-' + page);
  if (pg) pg.classList.add('active');
  const nl = document.querySelector(`.nav-link[data-page="${page}"]`);
  if (nl) nl.classList.add('active');

  const labels = { overview: 'Overview', agents: 'Pipelines & Agents', datasets: 'Test Scenarios', golden: 'Generate Mock Data', evaluate: 'Run Pipeline Test', results: 'Pipeline Run Results' };
  document.getElementById('trailCurrent').textContent = labels[page] || page;
  S.currentPage = page;

  if (page === 'agents')    renderAgentsTable();
  if (page === 'datasets')  renderTable();
  if (page === 'evaluate')  refreshEval();
  if (page === 'results')   renderResults();
  if (page === 'overview')  renderActivity();

  document.getElementById('sidebar').classList.remove('open');
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

function refreshCounters() {
  const ds = S.datasets.length;
  const rs = S.results.length;
  const de = S.results.filter(r => r.framework === 'deepeval').length;
  const rg = S.results.filter(r => r.framework === 'ragas').length;
  const ag = S_agents ? S_agents.length : 0;
  set('kpiDs', ds);
  set('kpiRuns', rs);
  set('kpiRG', rg);
  set('navDsCount', ds);
  set('navResultsCount', rs);
  set('navAgentCount', ag);
  if (ds > 0) document.getElementById('sn1')?.classList.add('done');
  if (rs > 0) {
    document.getElementById('sn3')?.classList.add('done');
    document.getElementById('sn4')?.classList.add('done');
  }
}

/* ─── ACTIVITY ─── */
function addActivity(color, text) {
  S.activity.unshift({ color, text, time: Date.now() });
  if (S.activity.length > 10) S.activity.pop();
  if (S.currentPage === 'overview') renderActivity();
}

function renderActivity() {
  const el = document.getElementById('activityFeed');
  if (!el) return;
  if (S.activity.length === 0) {
    el.innerHTML = '<div class="no-data" style="padding:16px 20px">No activity yet — upload a dataset to begin.</div>';
    return;
  }
  el.innerHTML = S.activity.map(a => `
    <div class="act-item">
      <div class="act-dot ${a.color}"></div>
      <div class="act-text">${esc(a.text)}</div>
      <div class="act-time">${ago(a.time)}</div>
    </div>`).join('');
}

/* ─── DATASETS TABLE ─── */
function renderTable() {
  const q = S.filterQ.toLowerCase();
  const list = S.datasets.filter(d =>
    d.name.toLowerCase().includes(q) || (d.tags||'').toLowerCase().includes(q)
  );

  set('dsCount', `${list.length} dataset${list.length !== 1 ? 's' : ''}`);

  const body = document.getElementById('dsBody');
  if (!list.length) {
    body.innerHTML = `<tr class="empty-tr"><td colspan="7">
      <div class="no-data-full">
        ${S.datasets.length === 0
          ? 'No datasets yet — upload an Excel file to get started'
          : `No results matching "${S.filterQ}"`}
      </div></td></tr>`;
    return;
  }

  body.innerHTML = list.map(d => {
    const tags = d.tags
      ? d.tags.split(',').map(t => `<span class="tag">${esc(t.trim())}</span>`).join('')
      : '—';
    const sc = d.status === 'Ready' ? 'b-green' : d.status === 'Processing' ? 'b-amber' : 'b-red';
    return `
      <tr>
        <td><input type="checkbox" class="row-chk" data-id="${d.id}" onchange="updateBulk()" /></td>
        <td>
          <div style="font-weight:600;font-size:14px">${esc(d.name)}</div>
          ${d.description ? `<div style="font-size:12px;color:var(--t-muted);margin-top:2px">${esc(d.description.slice(0,70))}${d.description.length>70?'…':''}</div>` : ''}
        </td>
        <td style="font-weight:600">${d.questionCount.toLocaleString()}</td>
        <td><div class="tags">${tags}</div></td>
        <td style="color:var(--t-muted)">${fmtDate(d.uploadedAt)}</td>
        <td><span class="badge ${sc}">${d.status}</span></td>
        <td>
          <div class="row-acts">
            <button class="r-btn run" title="Quick run" onclick="quickRun('${d.id}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
            </button>
            <button class="r-btn" title="View / Edit" onclick="openView('${d.id}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="r-btn del" title="Delete" onclick="openDel('${d.id}')">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
            </button>
          </div>
        </td>
      </tr>`;
  }).join('');
}

function filterDs() {
  S.filterQ = document.getElementById('dsSearch').value;
  renderTable();
}

function toggleAll(el) {
  document.querySelectorAll('.row-chk').forEach(c => { c.checked = el.checked; });
  updateBulk();
}

function updateBulk() {
  const n = document.querySelectorAll('.row-chk:checked').length;
  document.getElementById('bulkBar').style.display = n > 0 ? 'flex' : 'none';
  document.getElementById('chkAll').indeterminate = n > 0 && n < S.datasets.length;
}

function bulkDel() {
  const ids = [...document.querySelectorAll('.row-chk:checked')].map(c => c.dataset.id);
  if (!ids.length) return;
  if (!confirm(`Delete ${ids.length} dataset(s)?`)) return;
  S.datasets = S.datasets.filter(d => !ids.includes(d.id));
  renderTable(); refreshCounters(); updateBulk();
  toast('s', `${ids.length} dataset(s) deleted`);
  if (S.currentPage === 'evaluate') refreshEval();
}


/* ─── AGENTS LOGIC ─── */
function openAgentModal() {
  document.getElementById('agentName').value = '';
  document.getElementById('agentDesc').value = '';
  document.getElementById('agentType').value = 'custom';
  document.getElementById('connectorType').value = 'rest_api';
  document.getElementById('agentEndpoint').value = '';
  document.getElementById('pythonClassPath').value = '';
  document.getElementById('agentTimeout').value = '30';
  toggleConnectorFields();
  openM('ovAgent');
}

function toggleConnectorFields() {
  const type = document.getElementById('connectorType').value;
  if (type === 'rest_api') {
    show('fieldEndpoint');
    hide('fieldPython');
  } else {
    hide('fieldEndpoint');
    show('fieldPython');
  }
}

async function submitAgent() {
  const name = document.getElementById('agentName').value.trim();
  const desc = document.getElementById('agentDesc').value.trim();
  const agent_type = document.getElementById('agentType').value.trim();
  const connector_type = (document.getElementById('connectorType').value || '').toLowerCase();
  const normalizedConnectorType = connector_type === 'python' ? 'python_class' : connector_type;
  const endpoint = document.getElementById('agentEndpoint').value.trim();
  const python_class_path = document.getElementById('pythonClassPath').value.trim();
  const timeout = parseInt(document.getElementById('agentTimeout').value) || 30;

  if (!name) { toast('w', 'Please enter an agent name'); return; }

  const payload = {
    agent_name: name,
    description: desc,
    agent_type: agent_type,
    connector_type: normalizedConnectorType,
    endpoint: normalizedConnectorType === 'rest_api' ? endpoint : null,
    python_class_path: normalizedConnectorType === 'python_class' ? python_class_path : null,
    timeout_seconds: timeout,
    auth_config: { auth_type: 'none' }
  };

  try {
    const res = await fetchApi('/agents', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    toast('s', `Agent "${name}" registered successfully`);
    closeM('ovAgent');
    
    // Refresh agent data
    const agents = await fetchApi('/agents');
    S_agents = agents;
    
    // Update evaluate dropdown
    updateAgentDropdown();
    
    refreshCounters();
    if (S.currentPage === 'agents') renderAgentsTable();
  } catch (e) {
    toast('e', 'Failed to register agent: ' + e.message);
  }
}

function renderAgentsTable() {
  const body = document.getElementById('agentBody');
  if (!S_agents || S_agents.length === 0) {
    body.innerHTML = `<tr class="empty-tr"><td colspan="5"><div class="no-data-full">No pipelines/agents registered yet — register an agent to run evaluations</div></td></tr>`;
    return;
  }

  body.innerHTML = S_agents.map(a => `
    <tr>
      <td style="font-weight:600;font-size:14px">${esc(a.agent_name)}</td>
      <td><span class="badge b-blue">${esc(a.connector_type)}</span></td>
      <td style="color:var(--t-muted);font-family:monospace;font-size:12px">${esc(a.connector_type === 'rest_api' ? a.endpoint : a.python_class_path || 'N/A')}</td>
      <td><span class="badge ${a.is_active ? 'b-green' : 'b-gray'}">${a.is_active ? 'Active' : 'Inactive'}</span></td>
      <td>
        <div class="row-acts">
          <button class="r-btn run" title="Check Health" onclick="checkAgentHealth('${a.id}')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          </button>
          <button class="r-btn del" title="Delete" onclick="deleteAgent('${a.id}')">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

async function deleteAgent(id) {
  if (!confirm('Are you sure you want to delete this agent?')) return;
  try {
    await fetchApi(`/agents/${id}`, { method: 'DELETE' });
    toast('s', 'Agent deleted');
    S_agents = S_agents.filter(a => a.id !== id);
    
    // Update evaluate dropdown
    updateAgentDropdown();
    
    refreshCounters();
    renderAgentsTable();
  } catch (e) {
    toast('e', 'Failed to delete agent: ' + e.message);
  }
}

async function checkAgentHealth(id) {
  try {
    toast('i', 'Checking agent health...');
    const res = await fetchApi(`/agents/${id}/health`, { method: 'POST' });
    if (res.healthy) {
      toast('s', `Agent is healthy (Latency: ${res.latency_ms.toFixed(1)}ms)`);
    } else {
      toast('w', `Agent unhealthy: ${res.message}`);
    }
  } catch (e) {
    toast('e', 'Health check request failed: ' + e.message);
  }
}

/* ─── UPLOAD ─── */
function openUploadModal() {
  clearForm();
  openM('ovUpload');
}

function onFileSelect(inp) {
  const f = inp.files[0];
  if (!f) return;
  _file = f;
  show('mFilePrev');
  set('fpName', f.name);
  set('fpSize', fmtBytes(f.size));
  const nm = document.getElementById('inpName');
  if (nm && !nm.value) nm.value = f.name.replace(/\.(xlsx?|xls|txt)$/i, '');
}

function clearFile() {
  _file = null;
  document.getElementById('fileIn').value = '';
  hide('mFilePrev');
}

function clearForm() {
  _file = null;
  ['fileIn','inpName','inpTags','inpDesc'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  hide('mFilePrev');
}

async function submitUpload() {
  const name = document.getElementById('inpName').value.trim();
  if (!name)  { toast('w', 'Please enter a dataset name'); return; }
  if (!_file) { toast('w', 'Please select a scenario file'); return; }

  const formData = new FormData();
  formData.append('file', _file);
  
  try {
      openM('ovProg');
      document.getElementById('progMsg').textContent = 'Uploading dataset...';
      const dsRes = await fetchApi('/test-suites/upload', {
          method: 'POST',
          body: formData
      });
      closeM('ovProg');
      
      const ds = {
        id: dsRes.id,
        name: dsRes.name || name,
        tags: document.getElementById('inpTags').value.trim(),
        description: document.getElementById('inpDesc').value.trim(),
        fileName: _file.name,
        fileSize: _file.size,
        questionCount: dsRes.total_cases,
        status: 'Ready',
        uploadedAt: dsRes.created_at || new Date().toISOString(),
      };

      S.datasets.unshift(ds);
      closeM('ovUpload');
      clearForm();
      refreshCounters();
      renderTable();
      addActivity('blue', `Uploaded "${ds.name}" — ${ds.questionCount} questions`);
      toast('s', `"${ds.name}" uploaded successfully`);
      if (S.currentPage === 'evaluate') refreshEval();
  } catch (e) {
      closeM('ovProg');
      toast('e', 'Upload failed: ' + e.message);
  }
}

/* ─── VIEW / EDIT ─── */
function openView(id) {
  const d = S.datasets.find(x => x.id === id);
  if (!d) return;
  S.editId = id;
  S.isEditing = false;

  set('mViewTitle', d.name);
  set('mViewSub',   `${fmtDate(d.uploadedAt)} · ${d.questionCount.toLocaleString()} questions · ${d.fileName}`);
  document.getElementById('editToggle').textContent = 'Edit';
  document.getElementById('saveBtn').style.display = 'none';
  document.getElementById('mView').classList.remove('edit-mode');

  const tags = d.tags
    ? d.tags.split(',').map(t => `<span class="tag">${esc(t.trim())}</span>`).join(' ')
    : '—';

  const qs = sampleQs();

  document.getElementById('mViewBody').innerHTML = `
    <div class="de-grid">
      <div class="de-item">
        <div class="de-key">Name</div>
        <div class="de-val">${esc(d.name)}</div>
        <input class="de-inp" data-f="name" value="${esc(d.name)}" />
      </div>
      <div class="de-item">
        <div class="de-key">Status</div>
        <div class="de-val"><span class="badge b-green">${d.status}</span></div>
        <input class="de-inp" data-f="status" value="${d.status}" />
      </div>
      <div class="de-item">
        <div class="de-key">Questions</div>
        <div class="de-val" style="font-size:18px;font-weight:800">${d.questionCount.toLocaleString()}</div>
        <input class="de-inp" data-f="questionCount" type="number" value="${d.questionCount}" />
      </div>
      <div class="de-item">
        <div class="de-key">Uploaded</div>
        <div class="de-val" style="color:var(--t-muted)">${fmtDate(d.uploadedAt)}</div>
        <input class="de-inp" data-f="uploadedAt" value="${d.uploadedAt}" disabled />
      </div>
      <div class="de-item">
        <div class="de-key">File</div>
        <div class="de-val" style="color:var(--t-muted)">${esc(d.fileName)}</div>
        <input class="de-inp" data-f="fileName" value="${esc(d.fileName)}" disabled />
      </div>
      <div class="de-item">
        <div class="de-key">File Size</div>
        <div class="de-val" style="color:var(--t-muted)">${fmtBytes(d.fileSize)}</div>
        <input class="de-inp" data-f="fileSize" value="${fmtBytes(d.fileSize)}" disabled />
      </div>
      <div class="de-item" style="grid-column:1/-1">
        <div class="de-key">Tags</div>
        <div class="de-val">${tags}</div>
        <input class="de-inp" data-f="tags" value="${esc(d.tags||'')}" placeholder="tag1, tag2, …" />
      </div>
      <div class="de-item" style="grid-column:1/-1">
        <div class="de-key">Description</div>
        <div class="de-val" style="color:var(--t-sec)">${esc(d.description||'—')}</div>
        <input class="de-inp" data-f="description" value="${esc(d.description||'')}" />
      </div>
    </div>
    <div>
      <div class="rd-section-title" style="margin-bottom:10px">Sample Questions (Preview)</div>
      <div style="overflow-x:auto">
        <table class="tbl" style="font-size:13px">
          <thead><tr><th>#</th><th>Question</th><th>Ground Truth</th><th>Context</th></tr></thead>
          <tbody>
            ${qs.map((q,i)=>`
              <tr>
                <td style="color:var(--t-muted)">${i+1}</td>
                <td style="max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(q.q)}</td>
                <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--t-sec)">${esc(q.gt)}</td>
                <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--t-muted)">${esc(q.ctx)}</td>
              </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>`;

  openM('ovView');
}

function toggleEdit() {
  S.isEditing = !S.isEditing;
  document.getElementById('mView').classList.toggle('edit-mode', S.isEditing);
  document.getElementById('editToggle').textContent = S.isEditing ? 'Cancel' : 'Edit';
  document.getElementById('saveBtn').style.display = S.isEditing ? 'block' : 'none';
}

function saveEdit() {
  const d = S.datasets.find(x => x.id === S.editId);
  if (!d) return;
  document.querySelectorAll('.de-inp:not([disabled])').forEach(el => {
    const f = el.dataset.f;
    if (f === 'questionCount') d.questionCount = parseInt(el.value) || d.questionCount;
    else if (f) d[f] = el.value;
  });
  closeM('ovView');
  renderTable();
  if (S.currentPage === 'evaluate') refreshEval();
  toast('s', 'Dataset updated');
}

/* ─── DELETE ─── */
function openDel(id) {
  S.deleteId = id;
  const d = S.datasets.find(x => x.id === id);
  set('delName', d ? d.name : '');
  openM('ovDel');
}

async function confirmDel() {
  const d = S.datasets.find(x => x.id === S.deleteId);
  try {
      await fetchApi(`/test-suites/${S.deleteId}`, { method: 'DELETE' });
      S.datasets = S.datasets.filter(x => x.id !== S.deleteId);
      S.results  = S.results.filter(x => x.datasetId !== S.deleteId);
      if (S.selDataset === S.deleteId) S.selDataset = null;
      closeM('ovDel');
      renderTable(); renderResults(); refreshCounters();
      addActivity('red', `Deleted "${d?.name||'dataset'}"`);
      toast('s', `"${d?.name}" deleted`);
      if (S.currentPage === 'evaluate') refreshEval();
  } catch(e) {
      toast('e', 'Failed to delete: ' + e.message);
  }
}

/* ─── EVALUATE ─── */
function refreshEval() {
  renderDsPicker();
  renderMetrics();
  refreshSummary();
}

function renderDsPicker() {
  const g = document.getElementById('dsPickGrid');
  if (!S.datasets.length) {
    g.innerHTML = '<div class="no-data">No datasets found. <button class="inline-link" onclick="navigateTo(\'datasets\')">Upload one →</button></div>';
    return;
  }
  g.innerHTML = S.datasets.map(d => `
    <div class="ds-opt ${S.selDataset===d.id?'sel':''}" onclick="selDs('${d.id}')">
      <div class="ds-opt-ic">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </div>
      <div class="ds-opt-info">
        <div class="ds-opt-name">${esc(d.name)}</div>
        <div class="ds-opt-meta">${d.questionCount.toLocaleString()} questions · ${fmtDate(d.uploadedAt)}</div>
      </div>
      <div class="ds-opt-radio"></div>
    </div>`).join('');
}

function selDs(id) {
  S.selDataset = id;
  renderDsPicker();
  refreshSummary();
}

function pickFramework(fw) {
  S.selFramework = fw;
  S.selMetrics = [];
  document.getElementById('fwDeepEval')?.classList.toggle('active', fw === 'deepeval');
  document.getElementById('fwRagas')?.classList.toggle('active', fw === 'ragas');
  document.getElementById('fwDataInt')?.classList.toggle('active', fw === 'data_integrity');
  document.getElementById('fwDataTrans')?.classList.toggle('active', fw === 'data_transformation');
  renderMetrics();
  refreshSummary();
}

function renderMetrics() {
  const list = METRICS[S.selFramework];
  const g = document.getElementById('metricsGrid');
  g.innerHTML = list.map(m => `
    <div class="metric-tile ${S.selMetrics.includes(m.id)?'on':''}" onclick="togMetric('${m.id}')" id="mt-${m.id}">
      <div class="mt-chk">
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
      </div>
      <div class="mt-body">
        <div class="mt-name">${esc(m.name)}</div>
        <div class="mt-desc">${esc(m.desc)}</div>
        <span class="mt-cat ${m.cat}">${m.cat}</span>
      </div>
    </div>`).join('');
  set('selCount', `${S.selMetrics.length} selected`);
}

function togMetric(id) {
  const i = S.selMetrics.indexOf(id);
  if (i === -1) S.selMetrics.push(id);
  else S.selMetrics.splice(i, 1);
  const t = document.getElementById('mt-' + id);
  if (t) t.classList.toggle('on', S.selMetrics.includes(id));
  set('selCount', `${S.selMetrics.length} selected`);
  refreshSummary();
}

function allMetrics() {
  S.selMetrics = METRICS[S.selFramework].map(m => m.id);
  renderMetrics();
  refreshSummary();
}

function clearMetrics() {
  S.selMetrics = [];
  renderMetrics();
  refreshSummary();
}

function refreshSummary() {
  const d = S.datasets.find(x => x.id === S.selDataset);
  set('rsDs',  d ? `${d.name} (${d.questionCount.toLocaleString()} questions)` : '— not selected');
  
  let fwName = 'DeepEval';
  if (S.selFramework === 'ragas') fwName = 'RAGAS';
  if (S.selFramework === 'data_integrity') fwName = 'Data Integrity';
  if (S.selFramework === 'data_transformation') fwName = 'Data Transformation';
  
  set('rsFw',  fwName);
  set('rsMet', `${S.selMetrics.length} metric${S.selMetrics.length!==1?'s':''} selected`);
  set('rsMod', document.getElementById('runModel')?.value || 'GPT-4o');
  set('rsThr', parseFloat(document.getElementById('thrSlider')?.value||0.5).toFixed(2));
}

function onThr(v) {
  set('thrVal', parseFloat(v).toFixed(2));
  refreshSummary();
}

function resetEval() {
  S.selDataset = null;
  S.selMetrics = [];
  S.selFramework = 'deepeval';
  document.getElementById('runName').value = '';
  document.getElementById('runModel').value = 'gpt-4o';
  document.getElementById('thrSlider').value = 0.5;
  document.getElementById('runNotes').value = '';
  set('thrVal', '0.50');
  pickFramework('deepeval');
  renderDsPicker();
  refreshSummary();
  toast('i', 'Evaluation reset');
}

function quickRun(id) {
  S.selDataset = id;
  navigateTo('evaluate');
  setTimeout(() => document.getElementById('ec1')?.scrollIntoView({ behavior:'smooth', block:'start' }), 150);
}

/* ─── RUN ─── */
async function doRun() {
  if (!S.selDataset)       { toast('w', 'Please select a question set'); return; }
  if (!S.selMetrics.length){ toast('w', 'Please select at least one metric'); return; }

  const name  = document.getElementById('runName').value.trim()
    || `Run — ${new Date().toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'})}`;
  const model = document.getElementById('runModel').value;
  const thr   = parseFloat(document.getElementById('thrSlider').value);
  const notes = document.getElementById('runNotes').value.trim();
  const ds    = S.datasets.find(x => x.id === S.selDataset);

  openM('ovProg');
  runProgress(name, ds, model, thr, notes);
}

async function runProgress(name, ds, model, thr, notes) {
  const steps = [
    'Initializing Run...',
    'Running evaluations...',
    'Computing metric scores...',
    'Generating report...'
  ];

  const sl = document.getElementById('progStepList');
  sl.innerHTML = steps.map((s, i) => `
    <div class="ps ${i===0?'active':''}" id="ps${i}">
      <span class="ps-dot"></span>${s}
    </div>`).join('');

  document.getElementById('progMsg').textContent = "Running benchmark on backend...";

  try {
      // Use selected metrics as evaluator_names instead of just framework
      // Each metric ID (e.g., 'exact_match', 'latency', 'security') maps to a registered evaluator
      const evaluators = S.selMetrics.length > 0 ? S.selMetrics : [S.selFramework];
      
      const runConfig = {
          agent_id: model,
          test_suite_id: ds.id,
          evaluator_names: evaluators,
          evaluator_configs: {},
          parallel: false
      };
      const res = await fetchApi('/executions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(runConfig)
      });
      
      closeM('ovProg');
      finishRun(name, ds, model, thr, notes, res);
  } catch (e) {
      closeM('ovProg');
      toast('e', 'Run failed: ' + e.message);
  }
}

function finishRun(name, ds, model, thr, notes, res) {
  const avg = res.overall_score || 0;
  const scores = {};
  
  if (res.test_results && res.test_results.length > 0) {
      // Just mock mapping for now, since actual backend result format varies
      res.test_results[0].evaluation_results.forEach(er => {
          scores[er.evaluator_name] = {
              name: er.evaluator_name,
              cat: 'quality',
              score: er.score
          };
      });
  }

  const r = {
    id:           res.run_id,
    name,
    datasetId:    ds.id,
    datasetName:  ds.name,
    framework:    S.selFramework,
    model,
    threshold:    thr,
    notes,
    scores,
    avg,
    questionCount: res.total_tests || ds.questionCount,
    metricCount:  Object.keys(scores).length || 1,
    runAt:        res.started_at || new Date().toISOString(),
    passed:       res.passed_tests === res.total_tests,
  };

  S.results.unshift(r);
  refreshCounters();
  addActivity('green', `Completed "${name}" — avg score ${(avg*100).toFixed(1)}%`);
  toast('s', `Benchmark complete! Average score: ${(avg*100).toFixed(1)}%`);
  navigateTo('results');
}

/* ─── GOLDEN SET GENERATION ─── */
function generateGoldenSet() {
  const ctx = document.getElementById('goldContext').value.trim();
  const num = parseInt(document.getElementById('goldNum').value, 10);
  const model = document.getElementById('goldModel').value;

  if (!ctx) {
    toast('w', 'Please provide source context to generate questions.');
    return;
  }
  if (isNaN(num) || num < 1 || num > 500) {
    toast('w', 'Please enter a valid number of questions (1-500).');
    return;
  }

  // Simulate API call and generation
  openM('ovProg');
  const steps = [
    'Parsing source context…',
    `Initializing ${model}…`,
    'Generating question and answer pairs…',
    'Extracting ground truth context…',
    'Finalizing dataset formatting…'
  ];

  const sl = document.getElementById('progStepList');
  sl.innerHTML = steps.map((s, i) => `
    <div class="ps ${i===0?'active':''}" id="ps${i}">
      <span class="ps-dot"></span>${s}
    </div>`).join('');

  let pct = 0, stepIdx = 0;
  const arc = document.getElementById('progArc');
  const circ = 201.1;

  const iv = setInterval(() => {
    pct = Math.min(pct + Math.random() * 8 + 2, 100);
    arc.style.strokeDashoffset = circ - (pct / 100) * circ;
    set('progPct', Math.floor(pct) + '%');
    document.getElementById('progBar').style.width = pct + '%';

    const nsi = Math.floor((pct / 100) * steps.length);
    while (stepIdx < nsi && stepIdx < steps.length) {
      const old = document.getElementById('ps' + stepIdx);
      if (old) { old.classList.remove('active'); old.classList.add('done'); }
      stepIdx++;
      const cur = document.getElementById('ps' + stepIdx);
      if (cur) cur.classList.add('active');
    }
    set('progMsg', steps[Math.min(stepIdx, steps.length - 1)]);

    if (pct >= 100) {
      clearInterval(iv);
      setTimeout(() => { 
        closeM('ovProg'); 
        
        // Add new dataset
        const ds = {
          id: uid(),
          name: `Golden Set — ${model} (${num} Qs)`,
          tags: 'golden, generated, auto',
          description: 'Automatically generated golden set from provided context.',
          fileName: 'generated_golden_set.xlsx',
          fileSize: num * 1250, // rough estimate bytes
          questionCount: num,
          status: 'Ready',
          uploadedAt: new Date().toISOString(),
        };
        S.datasets.unshift(ds);
        refreshCounters();
        addActivity('blue', `Generated Golden Set with ${num} questions using ${model}`);
        toast('s', 'Golden set generated successfully!');
        
        // Reset form
        document.getElementById('goldContext').value = '';
        document.getElementById('goldInstructions').value = '';
        
        navigateTo('datasets');
      }, 600);
    }
  }, 120);
}

/* ─── RESULTS ─── */
function renderResults() {
  const el = document.getElementById('resultsList');
  if (S.results.length === 0) {
    el.innerHTML = `
      <div class="results-empty">
        <div class="results-empty-icon">
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
            <line x1="18" y1="20" x2="18" y2="10"/>
            <line x1="12" y1="20" x2="12" y2="4"/>
            <line x1="6" y1="20" x2="6" y2="14"/>
          </svg>
        </div>
        <div class="results-empty-title">No results yet</div>
        <div class="results-empty-sub">Run an evaluation to see detailed metric scores here</div>
        <button class="btn-primary" onclick="navigateTo('evaluate')" style="margin-top:18px">Start Evaluation</button>
      </div>`;
    return;
  }

  el.innerHTML = S.results.map(r => buildResultCard(r)).join('');
}

function buildResultCard(r) {
  const scores  = Object.values(r.scores);
  const avgPct  = (r.avg * 100).toFixed(1);
  const avgCol  = scoreColor(r.avg);
  const fwBadge = r.framework === 'deepeval'
    ? `<span class="badge b-blue">DeepEval</span>`
    : `<span class="badge b-gray">RAGAS</span>`;
  const passBadge = r.passed
    ? `<span class="badge b-green">Passed</span>`
    : `<span class="badge b-red">Below threshold</span>`;

  // Show top 8 metrics as bars
  const visible = scores.slice(0, 8);

  return `
    <div class="rc" onclick="openResult('${r.id}')">
      <div class="rc-top">
        <div>
          <div class="rc-title">${esc(r.name)}</div>
          <div class="rc-meta">
            <span>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <ellipse cx="12" cy="5" rx="9" ry="3"/>
                <path d="M3 5v6c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/>
              </svg>
              ${esc(r.datasetName)}
            </span>
            <span>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              ${fmtDate(r.runAt)}
            </span>
            <span>${r.questionCount.toLocaleString()} questions</span>
            <span>${r.metricCount} metrics</span>
            <span>Threshold: ${r.threshold.toFixed(2)}</span>
          </div>
        </div>
        <div class="rc-right">
          ${passBadge}
          ${fwBadge}
          <div class="rc-avg-score" style="color:${avgCol}">${avgPct}%</div>
          <div class="rc-avg-label">Average Score</div>
        </div>
      </div>

      <div class="rc-metrics">
        ${visible.map(s => {
          const pct = (s.score * 100).toFixed(1);
          const col = scoreColor(s.score);
          const barW = (s.score * 100).toFixed(1);
          return `
            <div class="rc-metric-row">
              <div class="rc-metric-name">${esc(s.name)}</div>
              <div class="rc-metric-bar-wrap">
                <div class="rc-metric-bar" style="width:${barW}%;background:${col}"></div>
              </div>
              <div class="rc-metric-pct" style="color:${col}">${pct}%</div>
            </div>`;
        }).join('')}
        ${scores.length > 8 ? `<div style="font-size:12px;color:var(--t-muted);margin-top:2px">+${scores.length-8} more metrics — click to view all</div>` : ''}
      </div>

      <div class="rc-foot">
        <div class="rc-foot-left">
          <span style="font-size:13px;color:var(--t-muted)">Model: <strong style="color:var(--t)">${esc(r.model)}</strong></span>
          ${r.notes ? `<span style="font-size:12px;color:var(--t-muted)">· ${esc(r.notes.slice(0,60))}${r.notes.length>60?'…':''}</span>` : ''}
        </div>
        <div class="rc-foot-right">
          <button class="rc-act" title="View details" onclick="openResult('${r.id}');event.stopPropagation()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
          </button>
          <button class="rc-act del" title="Delete" onclick="delResult('${r.id}');event.stopPropagation()">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/></svg>
          </button>
        </div>
      </div>
    </div>`;
}

function delResult(id) {
  S.results = S.results.filter(r => r.id !== id);
  renderResults();
  refreshCounters();
  toast('s', 'Result deleted');
}

function openResult(id) {
  const r = S.results.find(x => x.id === id);
  if (!r) return;
  S.resultViewId = id;

  const avgPct = (r.avg * 100).toFixed(2);
  set('rdTitle', r.name);
  set('rdSub', `${r.framework === 'deepeval' ? 'DeepEval' : 'RAGAS'} · ${esc(r.datasetName)} · ${fmtDate(r.runAt)}`);

  const scores = Object.values(r.scores);

  document.getElementById('rdBody').innerHTML = `
    <!-- Overview info -->
    <div class="rd-section">
      <div class="rd-section-title">Run Information</div>
      <div class="rd-info-grid">
        <div class="rd-info-box">
          <div class="rd-info-key">Dataset</div>
          <div class="rd-info-val">${esc(r.datasetName)}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Framework</div>
          <div class="rd-info-val">${r.framework === 'deepeval' ? 'DeepEval' : 'RAGAS'}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Judge Model</div>
          <div class="rd-info-val">${esc(r.model)}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Questions</div>
          <div class="rd-info-val">${r.questionCount.toLocaleString()}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Pass Threshold</div>
          <div class="rd-info-val">${r.threshold.toFixed(2)}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Verdict</div>
          <div class="rd-info-val" style="color:${r.passed?'var(--green)':'var(--red)'}">
            ${r.passed ? '✓ Passed' : '✗ Below threshold'}
          </div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Average Score</div>
          <div class="rd-info-val" style="font-size:22px;font-weight:800;color:${scoreColor(r.avg)}">${avgPct}%</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Metrics Evaluated</div>
          <div class="rd-info-val">${r.metricCount}</div>
        </div>
        <div class="rd-info-box">
          <div class="rd-info-key">Run Date</div>
          <div class="rd-info-val">${fmtDate(r.runAt)}</div>
        </div>
      </div>
      ${r.notes ? `<div style="padding:11px 14px;background:var(--bg-raised);border:1px solid var(--border);border-radius:var(--radius);font-size:13px;color:var(--t-sec)"><strong>Notes:</strong> ${esc(r.notes)}</div>` : ''}
    </div>

    <!-- Detailed metric scores -->
    <div class="rd-section">
      <div class="rd-section-title">Metric Breakdown</div>
      <div class="rd-metrics-detail">
        ${scores.map(s => {
          const pct = (s.score * 100).toFixed(2);
          const col = scoreColor(s.score);
          const verdict = s.score >= r.threshold
            ? `<span class="badge b-green">Pass</span>`
            : `<span class="badge b-red">Fail</span>`;
          const catBadge = s.cat
            ? `<span class="mt-cat ${s.cat}" style="display:inline-block">${s.cat}</span>`
            : '';
          return `
            <div class="rd-metric-row">
              <div class="rd-m-name">
                ${esc(s.name)}
                ${catBadge}
              </div>
              <div class="rd-m-bar-wrap">
                <div class="rd-m-bar" style="width:${pct}%;background:${col}"></div>
              </div>
              <div class="rd-m-pct" style="color:${col}">${pct}%</div>
              <div class="rd-m-verdict">${verdict}</div>
            </div>`;
        }).join('')}
      </div>
    </div>`;

  openM('ovResult');
}

function dlResult() {
  toast('i', 'Download would export this result as CSV');
}

function exportCSV() {
  if (!S.results.length) { toast('i', 'No results to export'); return; }
  toast('i', 'Would download all results as CSV');
}

/* ─── MODALS ─── */
function openM(id)  { document.getElementById(id)?.classList.add('open'); }
function closeM(id) { document.getElementById(id)?.classList.remove('open'); }

document.querySelectorAll('.overlay').forEach(el => {
  el.addEventListener('click', e => {
    if (e.target === el) closeM(el.id);
  });
});

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') document.querySelectorAll('.overlay.open').forEach(x => x.classList.remove('open'));
});

window.addEventListener('DOMContentLoaded', () => {
  bootstrapApp();
});

// Dropzone drag/drop
const mDz = document.getElementById('mDz');
mDz?.addEventListener('dragover', e => { e.preventDefault(); mDz.classList.add('dz-over'); });
mDz?.addEventListener('dragleave', () => mDz.classList.remove('dz-over'));
mDz?.addEventListener('drop', e => {
  e.preventDefault();
  mDz.classList.remove('dz-over');
  const f = e.dataTransfer.files[0];
  if (f) {
    _file = f; show('mFilePrev');
    set('fpName', f.name); set('fpSize', fmtBytes(f.size));
    const nm = document.getElementById('inpName');
    if (nm && !nm.value) nm.value = f.name.replace(/\.(xlsx?)$/i, '');
  }
});

const dz = document.getElementById('dropzone');
dz?.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dz-over'); });
dz?.addEventListener('dragleave', () => dz.classList.remove('dz-over'));
dz?.addEventListener('drop', e => {
  e.preventDefault();
  dz.classList.remove('dz-over');
  openUploadModal();
  const f = e.dataTransfer.files[0];
  if (f) setTimeout(() => {
    _file = f; show('mFilePrev');
    set('fpName', f.name); set('fpSize', fmtBytes(f.size));
    const nm = document.getElementById('inpName');
    if (nm && !nm.value) nm.value = f.name.replace(/\.(xlsx?)$/i, '');
  }, 120);
});

/* ─── TOAST ─── */
const TICS = {
  s: `<svg class="t-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`,
  e: `<svg class="t-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>`,
  i: `<svg class="t-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
  w: `<svg class="t-ic" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
};

function toast(type, msg) {
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `${TICS[type]||TICS.i}<span>${esc(msg)}</span>`;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 220); }, 3600);
}

/* ─── HELPERS ─── */
function uid()      { return Date.now().toString(36) + Math.random().toString(36).slice(2,7); }
function esc(s)     { return String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function set(id,v)  { const e=document.getElementById(id); if(e) e.textContent=v; }
function show(id)   { const e=document.getElementById(id); if(e) e.style.display='block'; }
function hide(id)   { const e=document.getElementById(id); if(e) e.style.display='none'; }

function fmtBytes(b) {
  if (!b) return '—';
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(1) + ' MB';
}
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});
}
function ago(ts) {
  const d = (Date.now() - ts) / 1000;
  if (d < 60) return 'just now';
  if (d < 3600) return Math.floor(d/60) + 'm ago';
  if (d < 86400) return Math.floor(d/3600) + 'h ago';
  return fmtDate(new Date(ts).toISOString());
}
function scoreColor(s) {
  if (s >= 0.7) return 'var(--green)';
  if (s >= 0.5) return 'var(--amber)';
  return 'var(--red)';
}
function sampleQs() {
  return [
    { q:'What is retrieval-augmented generation?',   gt:'RAG combines document retrieval with language model generation.',    ctx:'RAG systems retrieve context before generating answers.' },
    { q:'How does semantic search differ from keyword search?', gt:'Semantic search uses meaning; keyword search matches exact terms.', ctx:'Embeddings power semantic search by capturing meaning.' },
    { q:'What is a vector database?',                gt:'A database optimised for storing and querying high-dim vectors.',    ctx:'Vector DBs enable similarity search at scale.' },
    { q:'Define hallucination in LLMs.',             gt:'LLM hallucination is generating false info presented as true.',      ctx:'Hallucination is a key reliability issue in LLMs.' },
    { q:'What is prompt engineering?',               gt:'Crafting inputs to guide LLM outputs effectively.',                  ctx:'Prompt design greatly influences model behaviour.' },
  ];
}



/* ─── INIT ─── */
document.addEventListener('DOMContentLoaded', async () => {
  await fetchInitialData();
  renderTable();
  renderMetrics();
  renderActivity();
  refreshSummary();
  document.getElementById('runModel')?.addEventListener('change', refreshSummary);
});

async function fetchInitialData() {
  try {
    const [ds, runs, agents] = await Promise.all([
      fetchApi('/test-suites'),
      fetchApi('/executions'),
      fetchApi('/agents')
    ]);
    
    // Map backend models to frontend expected shape
    S.datasets = ds.map(d => ({
      id: d.id,
      name: d.name,
      tags: d.metadata?.tags || '',
      description: d.description,
      fileName: d.source_file || 'unknown',
      fileSize: 0,
      questionCount: d.total_cases || 0,
      status: 'Ready',
      uploadedAt: d.created_at
    }));

    S.results = runs.map(r => ({
      id: r.run_id,
      name: `Run ${r.run_id.substring(0,6)}`,
      datasetId: r.suite_id,
      datasetName: r.suite_id, // we might want to map this properly if we can
      framework: 'deepeval', // Defaulting since backend doesn't return this in summary
      model: r.agent_name || r.agent_id,
      threshold: 0.5,
      notes: '',
      scores: {}, // Backend run summary doesn't have detailed scores, would need to fetch full result
      avg: r.overall_score || 0.0,
      questionCount: r.total_tests || 0,
      metricCount: 1,
      runAt: r.created_at || r.started_at,
      passed: r.passed_tests === r.total_tests
    }));

    S_agents = agents;
    updateAgentDropdown();

    refreshCounters();
  } catch (e) {
    console.error("Failed to fetch initial data", e);
  }
}

