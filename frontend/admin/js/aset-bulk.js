(() => {
'use strict';
function init(){
 if(!['admin','koordinator'].includes(window.PIJAR_USER?.peran))return;
 const toolbar=document.querySelector('.topbar-actions');
 if(!toolbar||document.getElementById('bulk-import-open'))return;
 const open=document.createElement('button');open.id='bulk-import-open';open.type='button';open.className='btn btn-success btn-sm';open.textContent='Bulk Import';toolbar.appendChild(open);
 const dialog=document.createElement('dialog');dialog.setAttribute('aria-labelledby','bulk-title');dialog.style.cssText='width:94%;max-width:850px;max-height:90vh;overflow:auto;border:1px solid #cbd5e1;border-radius:12px;padding:24px';
 dialog.innerHTML='<h3 id="bulk-title">Bulk Import Aset</h3><p>Excel dua sheet atau CSV aset. Maksimum 4 MB dan 1.000 baris total. Data lama tidak ditimpa.</p><p><button id="bulk-xlsx" type="button">Template Excel</button> <button id="bulk-csv" type="button">Template CSV</button></p><label for="bulk-file">Pilih berkas</label><input id="bulk-file" type="file" accept=".xlsx,.csv"><p><button id="bulk-preview" type="button">Pratinjau</button> <button id="bulk-save" type="button" disabled>Simpan Import</button> <button id="bulk-close" type="button">Tutup</button></p><p id="bulk-status" role="status" aria-live="polite"></p><div id="bulk-tables" style="overflow:auto"></div>';
 document.body.appendChild(dialog);
 const el=id=>dialog.querySelector('#'+id);let file=null,digest=null,busy=false;
 function status(text){el('bulk-status').textContent=text;}
 function lock(value){busy=value;for(const id of ['bulk-file','bulk-preview','bulk-close','bulk-xlsx','bulk-csv'])el(id).disabled=value;el('bulk-save').disabled=value||!digest;}
 function clear(){digest=null;el('bulk-save').disabled=true;el('bulk-tables').replaceChildren();}
 function table(title,rows){
  const caption=document.createElement('h4');caption.textContent=title;el('bulk-tables').appendChild(caption);if(!rows.length)return;
  const columns=Object.keys(rows[0]);const t=document.createElement('table');t.style.cssText='border-collapse:collapse;font-size:13px;min-width:600px';
  const tr=document.createElement('tr');for(const key of columns){const th=document.createElement('th');th.textContent=key;th.style.cssText='padding:8px;border:1px solid #cbd5e1';tr.appendChild(th);}t.appendChild(tr);
  for(const row of rows){const line=document.createElement('tr');for(const key of columns){const td=document.createElement('td');td.textContent=row[key]??'';td.style.cssText='padding:8px;border:1px solid #cbd5e1';line.appendChild(td);}t.appendChild(line);}el('bulk-tables').appendChild(t);
 }
 open.onclick=()=>dialog.showModal();el('bulk-close').onclick=()=>{if(!busy)dialog.close();};dialog.addEventListener('cancel',e=>{if(busy)e.preventDefault();});
 el('bulk-file').onchange=()=>{file=el('bulk-file').files[0]||null;clear();status('');};
 async function run(mode){
  if(busy)return;if(!file){status('Pilih berkas terlebih dahulu.');return;}
  if(file.size>4*1024*1024){clear();status('Berkas melebihi 4 MB.');return;}
  if(!/\.(xlsx|csv)$/i.test(file.name)){clear();status('Gunakan XLSX atau CSV.');return;}
  if(mode==='commit'&&(!digest||!window.confirm('Simpan seluruh batch ke PIJAR? Aset lama tidak ditimpa.')))return;
  lock(true);status(mode==='preview'?'Memeriksa berkas...':'Menyimpan batch...');
  try{
   const data=new FormData();data.append('file',file);if(mode==='commit'){data.append('confirm','yes');data.append('sha256',digest);}
   const r=await apiFetch(`${API}/api/aset/import/${mode}`,{method:'POST',body:data});if(!r)throw new Error('Sesi berakhir. Silakan login ulang.');
   let j;try{j=await r.json();}catch(e){throw new Error(`Respons server bukan JSON (HTTP ${r.status}).`);}
   if(!r.ok||!j.success)throw new Error(j.error||`Permintaan gagal (HTTP ${r.status}).`);
   if(mode==='preview'){
    clear();if(j.valid!==true||!j.sha256)throw new Error('Pratinjau belum valid.');digest=j.sha256;
    status(`${j.total_aset} aset dan ${j.total_lampu} lampu valid. Maksimal 20 baris pratinjau per jenis.`);table('Data aset',j.preview_aset||[]);table('Data lampu',j.preview_lampu||[]);
   }else{
    clear();file=null;el('bulk-file').value='';status(`Berhasil: ${j.total_aset} aset dan ${j.total_lampu} lampu disimpan.`);
    if(typeof isMobile==='function'&&isMobile())resetInfiniteLoad();else loadAset(1);
   }
  }catch(e){clear();status(e.message+(mode==='commit'?' Jika koneksi terputus, periksa daftar aset sebelum mencoba kembali.':''));}finally{lock(false);}
 }
 async function download(format){
  if(busy)return;lock(true);
  try{const r=await apiFetch(`${API}/api/aset/import/template?format=${format}`);if(!r||!r.ok)throw new Error('Template tidak dapat diunduh.');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=`template_import_pijar.${format}`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1500);}catch(e){status(e.message);}finally{lock(false);}
 }
 el('bulk-preview').onclick=()=>run('preview');el('bulk-save').onclick=()=>run('commit');el('bulk-xlsx').onclick=()=>download('xlsx');el('bulk-csv').onclick=()=>download('csv');
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
