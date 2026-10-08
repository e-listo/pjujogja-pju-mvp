(() => {
'use strict';
const MAX_BYTES = 4 * 1024 * 1024;
const STYLE_ID = 'bulk-import-style';
const CSS = `
#modal-bulk .modal{width:780px;}
#modal-bulk .bulk-intro{font-size:.85rem;color:#64748b;line-height:1.5;margin:-4px 0 2px;}
#modal-bulk .bulk-templates{display:flex;gap:8px;flex-wrap:wrap;}
#modal-bulk .bulk-hint{font-size:.75rem;color:#94a3b8;line-height:1.5;margin-top:8px;}
#modal-bulk code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:.76rem;color:#1a56db;}
#modal-bulk .bulk-drop{position:relative;display:flex;flex-direction:column;align-items:center;gap:4px;padding:20px 16px;border:2px dashed #cbd5e1;border-radius:10px;background:#f8fafc;color:#64748b;cursor:pointer;text-align:center;transition:border-color .2s,background .2s;}
#modal-bulk .bulk-drop:hover,#modal-bulk .bulk-drop.drag,#modal-bulk .bulk-drop:focus-within{border-color:#1a56db;background:#eff6ff;}
#modal-bulk .bulk-drop.has-file{border-style:solid;border-color:#1a56db;background:#eff6ff;}
#modal-bulk .bulk-drop.is-disabled{opacity:.6;cursor:not-allowed;}
#modal-bulk .bulk-file-input{position:absolute;width:1px;height:1px;opacity:0;overflow:hidden;pointer-events:none;}
#modal-bulk .bulk-drop-icon{font-size:1.6rem;line-height:1;}
#modal-bulk .bulk-drop-title{font-size:.88rem;font-weight:600;color:#0f172a;word-break:break-all;}
#modal-bulk .bulk-drop-sub{font-size:.75rem;}
#modal-bulk .bulk-alert{margin-top:12px;padding:10px 12px;border-radius:8px;font-size:.84rem;line-height:1.5;border:1px solid #e2e8f0;background:#f8fafc;color:#64748b;}
#modal-bulk .bulk-alert[hidden]{display:none;}
#modal-bulk .bulk-alert.is-ok{background:#ecfdf5;border-color:#a7f3d0;color:#065f46;}
#modal-bulk .bulk-alert.is-err{background:#fef2f2;border-color:#fecaca;color:#991b1b;}
#modal-bulk .bulk-summary{display:flex;gap:6px;flex-wrap:wrap;margin-top:12px;}
#modal-bulk .bulk-note{font-weight:500;text-transform:none;letter-spacing:0;margin-left:6px;color:#94a3b8;}
#modal-bulk .table-wrap{border:1px solid #e2e8f0;border-radius:8px;}
#modal-bulk table{min-width:560px;font-size:.8rem;}
#modal-bulk td.bulk-code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.76rem;color:#1a56db;white-space:nowrap;}
#modal-bulk .btn:disabled,#modal-bulk .btn:disabled:hover{opacity:.45;cursor:not-allowed;}
#modal-bulk .btn[aria-disabled="true"]{opacity:.55;cursor:not-allowed;}
@media (max-width:640px){
#modal-bulk .modal{padding:18px;}
#modal-bulk .modal-actions{flex-wrap:wrap;}
#modal-bulk .modal-actions .btn{flex:1;justify-content:center;}
}`;

const STATUS_BADGE = {Menyala:'badge-hijau',Mati:'badge-merah',Rusak:'badge-merah',Redup:'badge-kuning','Dalam Pengerjaan':'badge-kuning'};
const ASET_COLS = [
  {label:'Kode Aset',get:r=>r.kode_aset,type:'kode'},
  {label:'Alamat',get:r=>r.alamat},
  {label:'Sektor',get:r=>r.sektor},
  {label:'Tahun',get:r=>r.tahun_pemasangan},
  {label:'Kategori Jalan',get:r=>r.kategori_jalan},
  {label:'Tinggi (m)',get:r=>r.tinggi_meter},
  {label:'Koordinat',get:r=>(r.lokasi_lat!=null&&r.lokasi_lng!=null)?`${r.lokasi_lat}, ${r.lokasi_lng}`:''},
  {label:'Status',get:r=>r.status,type:'status'}
];
const LAMPU_COLS = [
  {label:'Kode Aset',get:r=>r.kode_aset,type:'kode'},
  {label:'Jenis Lampu',get:r=>r.jenis_lampu},
  {label:'Daya (W)',get:r=>r.daya_watt},
  {label:'Merk',get:r=>r.merk},
  {label:'Tahun',get:r=>r.tahun_pasang},
  {label:'Status',get:r=>r.status_lampu,type:'status'}
];

function badge(text,cls){const s=document.createElement('span');s.className='badge '+cls;s.textContent=text;return s;}
function makeTable(rows,cols){
  const wrap=document.createElement('div');wrap.className='table-wrap';
  const t=document.createElement('table');
  const head=t.createTHead().insertRow();
  cols.forEach(c=>{const th=document.createElement('th');th.textContent=c.label;head.appendChild(th);});
  const body=t.createTBody();
  rows.forEach(r=>{
    const tr=body.insertRow();
    cols.forEach(c=>{
      const td=tr.insertCell();const v=c.get(r);
      if(v===''||v==null){td.textContent='—';}
      else if(c.type==='status'){td.appendChild(badge(String(v),STATUS_BADGE[v]||'badge-kuning'));}
      else{td.textContent=String(v);if(c.type==='kode')td.className='bulk-code';}
    });
  });
  wrap.appendChild(t);return wrap;
}
function sectionLabel(title,note){
  const d=document.createElement('div');d.className='section-label';d.textContent=title;
  if(note){const n=document.createElement('span');n.className='bulk-note';n.textContent=note;d.appendChild(n);}
  return d;
}
function formatSize(n){return n<1024*1024?`${(n/1024).toFixed(1)} KB`:`${(n/1024/1024).toFixed(2)} MB`;}

function init(){
  if(!['admin','koordinator'].includes(window.PIJAR_USER?.peran))return;
  const toolbar=document.querySelector('.topbar-actions');
  if(!toolbar||document.getElementById('bulk-import-open'))return;

  if(!document.getElementById(STYLE_ID)){
    const st=document.createElement('style');st.id=STYLE_ID;st.textContent=CSS;document.head.appendChild(st);
  }

  const open=document.createElement('button');
  open.id='bulk-import-open';open.type='button';open.className='btn btn-secondary btn-sm';
  open.innerHTML='📥 <span>Bulk Import</span>';
  toolbar.insertBefore(open,toolbar.querySelector('.btn-primary'));

  const overlay=document.createElement('div');
  overlay.className='modal-overlay';overlay.id='modal-bulk';
  overlay.innerHTML=`
  <div class="modal" role="dialog" aria-modal="true" aria-labelledby="bulk-title">
    <h3 id="bulk-title">📥 Bulk Import Aset</h3>
    <p class="bulk-intro">Tambahkan banyak aset beserta lampunya sekaligus dari berkas Excel. Data yang sudah ada <b>tidak ditimpa</b>.</p>
    <div class="section-label">1 · Unduh template</div>
    <div class="bulk-templates">
      <button type="button" class="btn btn-secondary btn-sm" id="bulk-xlsx">📗 Template Excel</button>
      <button type="button" class="btn btn-secondary btn-sm" id="bulk-csv" aria-disabled="true" title="CSV sementara dinonaktifkan">📄 Template CSV</button>
    </div>
    <p class="bulk-hint">Excel berisi sheet aset, lampu, referensi kategori/wilayah, dan panduan. Template CSV sementara dinonaktifkan; gunakan Excel. Format kode aset: <code>PJUP-UH2-26-001</code>.</p>
    <div class="section-label">2 · Pilih berkas</div>
    <label class="bulk-drop" id="bulk-drop">
      <input type="file" id="bulk-file" class="bulk-file-input" accept=".xlsx">
      <span class="bulk-drop-icon">📂</span>
      <span class="bulk-drop-title" id="bulk-file-name">Klik untuk memilih berkas, atau seret ke sini</span>
      <span class="bulk-drop-sub" id="bulk-file-sub">.xlsx · maksimum 4 MB · 1.000 baris</span>
    </label>
    <div id="bulk-status" class="bulk-alert" role="status" aria-live="polite" hidden></div>
    <div id="bulk-result"></div>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" id="bulk-close">Tutup</button>
      <button type="button" class="btn btn-primary" id="bulk-preview" disabled>🔍 Pratinjau</button>
      <button type="button" class="btn btn-success" id="bulk-save" disabled>💾 Simpan Import</button>
    </div>
  </div>`;
  document.body.appendChild(overlay);

  const $=id=>overlay.querySelector('#'+id);
  const fileInput=$('bulk-file'),drop=$('bulk-drop'),nameEl=$('bulk-file-name'),subEl=$('bulk-file-sub');
  const statusEl=$('bulk-status'),resultEl=$('bulk-result');
  const closeBtn=$('bulk-close'),previewBtn=$('bulk-preview'),saveBtn=$('bulk-save'),xlsxBtn=$('bulk-xlsx'),csvBtn=$('bulk-csv');
  let file=null,digest=null,summary=null,busy=false,lastFocus=null;

  function sync(){
    fileInput.disabled=busy;closeBtn.disabled=busy;xlsxBtn.disabled=busy;csvBtn.disabled=busy;
    previewBtn.disabled=busy||!file;saveBtn.disabled=busy||!digest;
    drop.classList.toggle('is-disabled',busy);
  }
  function setStatus(kind,text){
    statusEl.className='bulk-alert'+(kind?' is-'+kind:'');
    statusEl.textContent=text||'';
    statusEl.hidden=!text;
  }
  function resetResult(){digest=null;summary=null;resultEl.replaceChildren();}
  function paintFile(){
    drop.classList.toggle('has-file',!!file);
    nameEl.textContent=file?file.name:'Klik untuk memilih berkas, atau seret ke sini';
    subEl.textContent=file?formatSize(file.size):'.xlsx · maksimum 4 MB · 1.000 baris';
  }
  function pickFile(f){
    resetResult();setStatus('','');
    if(f&&!/\.(xlsx|csv)$/i.test(f.name)){file=null;fileInput.value='';paintFile();sync();setStatus('err','❌ Gunakan berkas Excel (.xlsx).');return;}
    if(f&&f.size>MAX_BYTES){file=null;fileInput.value='';paintFile();sync();setStatus('err','❌ Berkas melebihi 4 MB.');return;}
    file=f||null;paintFile();sync();
  }
  function renderPreview(j){
    resultEl.replaceChildren();
    const sum=document.createElement('div');sum.className='bulk-summary';
    sum.append(badge(`${j.total_aset} aset`,'badge-hijau'),badge(`${j.total_lampu} lampu`,'badge-hijau'));
    resultEl.appendChild(sum);
    const aset=j.preview_aset||[],lampu=j.preview_lampu||[];
    resultEl.appendChild(sectionLabel('Pratinjau aset',aset.length<j.total_aset?`menampilkan ${aset.length} dari ${j.total_aset} baris`:''));
    resultEl.appendChild(makeTable(aset,ASET_COLS));
    if(j.total_lampu>0){
      resultEl.appendChild(sectionLabel('Pratinjau lampu',lampu.length<j.total_lampu?`menampilkan ${lampu.length} dari ${j.total_lampu} baris`:''));
      resultEl.appendChild(makeTable(lampu,LAMPU_COLS));
    }
  }
  function askConfirm(s){
    const msg=`Simpan ${s.aset} aset dan ${s.lampu} lampu ke PIJAR? Data lama tidak ditimpa; bila ada yang gagal, seluruh batch dibatalkan.`;
    if(typeof pijarConfirm==='function')return pijarConfirm(msg,'📥','Ya, Simpan','btn-primary');
    return Promise.resolve(window.confirm(msg));
  }
  function refreshList(){
    try{if(typeof isMobile==='function'&&isMobile())resetInfiniteLoad();else loadAset(1);}catch(e){/* daftar akan dimuat ulang manual */}
  }
  async function run(mode){
    if(busy)return;
    if(!file){setStatus('err','❌ Pilih berkas terlebih dahulu.');return;}
    if(mode==='commit'){
      if(!digest||!summary)return;
      if(!await askConfirm(summary))return;
    }
    busy=true;sync();
    setStatus('',mode==='preview'?'⏳ Memeriksa berkas…':'⏳ Menyimpan batch…');
    try{
      const data=new FormData();data.append('file',file);
      if(mode==='commit'){data.append('confirm','yes');data.append('sha256',digest);}
      const r=await apiFetch(`${API}/api/aset/import/${mode}`,{method:'POST',body:data});
      if(!r)throw new Error('Sesi berakhir. Silakan login ulang.');
      let j;try{j=await r.json();}catch(e){throw new Error(`Respons server bukan JSON (HTTP ${r.status}).`);}
      if(!r.ok||!j.success)throw new Error(j.error||`Permintaan gagal (HTTP ${r.status}).`);
      if(mode==='preview'){
        if(j.valid!==true||!j.sha256)throw new Error('Pratinjau belum valid.');
        resetResult();digest=j.sha256;summary={aset:j.total_aset,lampu:j.total_lampu};
        renderPreview(j);
        setStatus('ok',`✅ Berkas valid: ${j.total_aset} aset dan ${j.total_lampu} lampu siap disimpan. Periksa pratinjau di bawah.`);
      }else{
        resetResult();file=null;fileInput.value='';paintFile();
        setStatus('ok',`✅ Berhasil: ${j.total_aset} aset dan ${j.total_lampu} lampu disimpan.`);
        if(typeof pijarToast==='function')pijarToast(`Import berhasil: ${j.total_aset} aset dan ${j.total_lampu} lampu`);
        refreshList();
      }
    }catch(e){
      resetResult();
      setStatus('err','❌ '+e.message+(mode==='commit'?' Jika koneksi terputus, periksa daftar aset sebelum mencoba kembali.':''));
    }finally{busy=false;sync();}
  }
  async function download(format){
    if(busy)return;
    busy=true;sync();setStatus('','⏳ Menyiapkan template…');
    try{
      const r=await apiFetch(`${API}/api/aset/import/template?format=${format}`);
      if(!r||!r.ok)throw new Error('Template tidak dapat diunduh.');
      const url=URL.createObjectURL(await r.blob());
      const a=document.createElement('a');a.href=url;a.download=`template_import_pijar.${format}`;
      document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1500);
      setStatus('ok','✅ Template diunduh.');
    }catch(e){setStatus('err','❌ '+e.message);}
    finally{busy=false;sync();}
  }
  function openModal(){
    lastFocus=document.activeElement;overlay.classList.add('show');
    (file?previewBtn:xlsxBtn).focus({preventScroll:true});
  }
  function closeModal(){
    if(busy)return;
    overlay.classList.remove('show');
    if(lastFocus&&lastFocus.focus)lastFocus.focus();
  }

  open.onclick=openModal;
  closeBtn.onclick=closeModal;
  overlay.addEventListener('click',e=>{if(e.target===overlay)closeModal();});
  document.addEventListener('keydown',e=>{
    if(e.key!=='Escape'||!overlay.classList.contains('show'))return;
    const konfirm=document.getElementById('modal-konfirmasi');
    if(konfirm&&konfirm.classList.contains('show'))return;
    closeModal();
  });
  fileInput.addEventListener('change',()=>pickFile(fileInput.files[0]||null));
  ['dragenter','dragover'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();if(!busy)drop.classList.add('drag');}));
  ['dragleave','drop'].forEach(ev=>drop.addEventListener(ev,e=>{e.preventDefault();drop.classList.remove('drag');}));
  drop.addEventListener('drop',e=>{if(!busy&&e.dataTransfer&&e.dataTransfer.files.length)pickFile(e.dataTransfer.files[0]);});
  previewBtn.onclick=()=>run('preview');
  saveBtn.onclick=()=>run('commit');
  xlsxBtn.onclick=()=>download('xlsx');
  csvBtn.onclick=()=>{if(busy)return;setStatus('','ℹ️ CSV sementara dinonaktifkan; gunakan Template Excel.');};
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
