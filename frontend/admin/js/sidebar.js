/** PIJAR: shared sidebar. Usage: sidebar.js?v=20261008, data-page="dashboard". */
(function () {
'use strict';
const isLapangan = location.pathname.includes('/lapangan/');
const adminBase = isLapangan ? '../' : '';
const lapBase = isLapangan ? '' : 'lapangan/';
const currentPage = (document.currentScript && document.currentScript.dataset.page) || '';
const logoutHref = adminBase + 'login.html';
function readUser() {
  try {
    const token = localStorage.getItem('pijar_token');
    if (!token) return {};
    let b = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    while (b.length % 4) b += '=';
    const payload = JSON.parse(new TextDecoder().decode(Uint8Array.from(atob(b), c => c.charCodeAt(0))));
    if (!payload.exp || payload.exp * 1000 <= Date.now()) return {};
    let stored = {};
    try { stored = JSON.parse(localStorage.getItem('pijar_user') || '{}'); } catch (e) {}
    return {...stored, ...payload, nama_lengkap: payload.nama || stored.nama_lengkap || stored.nama};
  } catch (e) { return {}; }
}
// Token hanya menentukan tampilan; API tetap memeriksa otorisasi.
const user = readUser();
const icons = {
 dashboard:'M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z',
 aset:'M12 2a7 7 0 1 1 0 14A7 7 0 0 1 12 2zm0 2a5 5 0 1 0 0 10A5 5 0 0 0 12 4zm0 2v4l3 2',
 laporan:'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8',
 pemeliharaan:'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z',
 wilayah:'M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15',
 regu:'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75',
 pengguna:'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
 lapor:'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z',
 penanganan:'M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11',
 more:'M5 12h.01M12 12h.01M19 12h.01',
 logout:'M9 5H5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h4M16 17l5-5-5-5M21 12H9'
};
const pages = [
 ['dashboard','Dashboard','index.html'], ['aset','Aset','aset.html'],
 ['laporan','Laporan','laporan.html'], ['pemeliharaan','Pemeliharaan','pemeliharaan.html'],
 ['wilayah','Wilayah','wilayah.html'], ['regu','Regu','regu.html']
].map(([id,label,file]) => ({id,label,href:adminBase + file,icon:icons[id]}));
if (user.peran === 'admin') pages.push({id:'pengguna',label:'Pengguna',href:adminBase+'pengguna.html',icon:icons.pengguna});
const lapangan = [
 {id:'form-laporan',label:'Form Lapor',href:lapBase+'lapor.html',icon:icons.lapor},
 {id:'form-penanganan',label:'Penanganan',href:lapBase+'form.html',icon:icons.penanganan}
];
const extra = [pages[4],{...pages[5],label:'Regu Lapangan'},...pages.filter(p=>p.id==='pengguna'),{...lapangan[0],label:'Form Laporan'},lapangan[1]];
const bottom = [pages[0],pages[1],pages[2],{...pages[3],label:'Pelihara'},{id:'more',label:'Lainnya',icon:icons.more}];
function svg(d) { return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`; }
function link(p, cls) { const active=p.id===currentPage; return `<a href="${p.href}" class="${cls}${active?' active':''}" ${active?'aria-current="page"':''}>${svg(p.icon)}<span>${p.label}</span></a>`; }
function account(prefix,cls) { return `<div class="${cls}"><div class="user-avatar" id="${prefix}-avatar">?</div><div class="user-info"><span class="account-caption">Akun masuk</span><span class="user-name" id="${prefix}-name">—</span><span class="user-role" id="${prefix}-role">—</span></div><button type="button" class="btn-logout" data-pijar-logout aria-label="Keluar dari akun" title="Keluar dari akun">${svg(icons.logout)}<span>Keluar</span></button></div>`; }
const footer=`&copy; ${new Date().getFullYear()} UPT Penerangan Jalan Umum &middot; Dinas PUPKP Kota Yogyakarta`;
const sidebar=`<aside class="pijar-sidebar" id="pijar-sidebar-el"><a href="${adminBase}index.html" class="sidebar-brand"><img class="brand-logo" src="/images/pijar_square.png" alt="Logo PIJAR" width="34" height="34" fetchpriority="high"><span class="brand-fallback" aria-hidden="true">🔆</span><div class="brand-text"><span class="brand-name">PIJAR</span><span class="brand-sub">PENGUATAN INVENTARISASI JARINGAN ASET YANG RESPONSIF</span></div></a><nav class="sidebar-nav" aria-label="Menu Utama"><div class="nav-group-label">Menu Utama</div>${pages.map(p=>link(p,'nav-item')).join('')}<div class="nav-group-label nav-group-lapangan">Lapangan</div>${lapangan.map(p=>link(p,'nav-item')).join('')}</nav>${account('pijar-user','sidebar-user')}<div class="sidebar-footer">${footer}</div></aside>`;
const mobile=`<nav class="pijar-bottom-nav" aria-label="Navigasi">${bottom.map(p=>p.id==='more'?`<button type="button" class="bn-item${extra.some(x=>x.id===currentPage)?' active':''}" id="pijar-more" aria-controls="pijar-drawer" aria-expanded="false">${svg(p.icon)}<span>${p.label}</span></button>`:link(p,'bn-item')).join('')}</nav><div class="pijar-drawer-overlay" id="pijar-drawer-overlay"></div><div class="pijar-drawer" id="pijar-drawer" role="dialog" aria-modal="true" aria-label="Menu lainnya" hidden><div class="drawer-heading"><span>Menu Lainnya</span><button type="button" id="pijar-drawer-close" class="drawer-close" aria-label="Tutup menu">&times;</button></div>${account('drawer-user','drawer-user')}<nav class="drawer-menu" aria-label="Menu tambahan">${extra.map(p=>link(p,'drawer-item')).join('')}</nav><div class="drawer-footer">${footer}</div></div>`;
const styles=`<style id="pijar-sidebar-css">
.pijar-sidebar{position:fixed;top:0;left:0;width:224px;height:100vh;background:#0f2236;color:#e2e8f0;display:flex;flex-direction:column;z-index:200;border-right:1px solid #ffffff12;box-sizing:border-box}
.pijar-sidebar .sidebar-brand{display:flex;align-items:center;gap:10px;padding:14px 16px;border-bottom:1px solid #ffffff14;text-decoration:none;flex-shrink:0}
.pijar-sidebar .brand-logo{width:34px;height:34px;object-fit:contain;flex-shrink:0;filter:drop-shadow(0 1px 6px #f9731659)}
.pijar-sidebar .brand-fallback{display:none;width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#f97316,#facc15);align-items:center;justify-content:center;flex-shrink:0}
.pijar-sidebar .brand-text{display:flex;flex-direction:column;min-width:0}
.pijar-sidebar .brand-name{font-size:1.1rem;font-weight:900;color:#facc15;letter-spacing:.07em;line-height:1}
.pijar-sidebar .brand-sub{font-size:.58rem;color:#94a3b8;line-height:1.5;margin-top:4px}
.pijar-sidebar .sidebar-nav{flex:1;min-height:0;padding:8px 0;overflow-y:auto;overflow-x:hidden}
.pijar-sidebar .nav-group-label{padding:8px 16px 3px;font-size:.6rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.1em}
.pijar-sidebar .nav-group-lapangan{margin-top:10px}
.pijar-sidebar .nav-item{display:flex;align-items:center;gap:9px;min-height:44px;box-sizing:border-box;padding:8px 16px;color:#cbd5e1;text-decoration:none;font-size:.82rem;border-left:3px solid transparent;white-space:nowrap}
.pijar-sidebar .nav-item svg,.pijar-drawer .drawer-item svg{width:18px;height:18px;flex-shrink:0}
.pijar-sidebar .nav-item:hover,.pijar-drawer .drawer-item:hover{background:#ffffff0d;color:#fff}
.pijar-sidebar .nav-item.active{background:#f973161f;color:#fff;font-weight:600;border-left-color:#f97316}
.pijar-sidebar .nav-item.active svg{stroke:#fb923c}
.pijar-sidebar .sidebar-user,.pijar-drawer .drawer-user{display:flex;align-items:center;gap:9px;border-top:1px solid #f973162e;background:linear-gradient(135deg,#f9731614,#ffffff06)}
.pijar-sidebar .sidebar-user{padding:14px 12px;min-height:84px;box-sizing:border-box;flex-shrink:0}
.pijar-sidebar .user-avatar,.pijar-drawer .user-avatar{width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#f97316,#c2410c);color:#fff;font-size:.9rem;font-weight:800;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid #fb923c80}
.pijar-sidebar .user-info,.pijar-drawer .user-info{flex:1;min-width:0;overflow:hidden}
.pijar-sidebar .account-caption,.pijar-drawer .account-caption{display:block;font-size:.56rem;color:#fb923c;text-transform:uppercase;letter-spacing:.08em;margin-bottom:3px}
.pijar-sidebar .user-name,.pijar-drawer .user-name{display:block;font-size:.75rem;font-weight:600;color:#f8fafc;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pijar-sidebar .user-role,.pijar-drawer .user-role{display:block;font-size:.65rem;color:#cbd5e1;margin-top:3px;text-transform:capitalize}
.pijar-sidebar .btn-logout,.pijar-drawer .btn-logout{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;min-width:44px;min-height:44px;padding:5px;background:#f9731614;border:1px solid #f9731640;color:#fdba74;font-family:inherit;font-size:.58rem;font-weight:600;cursor:pointer;border-radius:8px;flex-shrink:0}
.pijar-sidebar .btn-logout svg,.pijar-drawer .btn-logout svg{width:18px;height:18px}
.pijar-sidebar .btn-logout:hover,.pijar-drawer .btn-logout:hover{background:#f97316;border-color:#f97316;color:#fff}
.pijar-sidebar .sidebar-footer,.pijar-drawer .drawer-footer{color:#94a3b8;font-size:.65rem;line-height:1.6;text-align:center;border-top:1px solid #ffffff14}
.pijar-sidebar .sidebar-footer{padding:10px 14px;flex-shrink:0}
.pijar-sidebar .copyright,.pijar-drawer .copyright{display:block;margin-top:3px;font-size:.6rem}
.pijar-bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;min-height:60px;background:#0f2236;border-top:1px solid #ffffff1a;z-index:200;padding:0 4px;padding-bottom:env(safe-area-inset-bottom,0px)}
.pijar-bottom-nav .bn-item{display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;gap:3px;min-width:0;min-height:60px;box-sizing:border-box;color:#cbd5e1;text-decoration:none;font-family:inherit;font-size:.6rem;font-weight:500;padding:6px 0;border:0;border-top:2px solid transparent;background:transparent;cursor:pointer}
.pijar-bottom-nav .bn-item svg{width:20px;height:20px;flex-shrink:0}
.pijar-bottom-nav .bn-item.active{color:#fb923c;border-top-color:#f97316}
.pijar-drawer-overlay{display:none;position:fixed;inset:0;background:#0008;z-index:299;backdrop-filter:blur(2px)}
.pijar-drawer-overlay.show{display:block}
.pijar-drawer{position:fixed;bottom:0;left:0;right:0;background:#0f2236;color:#e2e8f0;border-radius:18px 18px 0 0;z-index:300;max-height:80vh;overflow-y:auto;padding-bottom:env(safe-area-inset-bottom,16px)}
.pijar-drawer[hidden]{display:none}
.pijar-drawer .drawer-heading{display:flex;align-items:center;justify-content:space-between;padding:10px 18px;font-size:.85rem;font-weight:700}
.pijar-drawer .drawer-close{width:44px;height:44px;border:0;border-radius:8px;background:transparent;color:#cbd5e1;font-size:1.5rem;cursor:pointer}
.pijar-drawer .drawer-user{padding:12px 18px;border-bottom:1px solid #ffffff12}
.pijar-drawer .drawer-menu{padding:10px 0}
.pijar-drawer .drawer-item{display:flex;align-items:center;gap:10px;min-height:44px;box-sizing:border-box;padding:12px 22px;color:#cbd5e1;text-decoration:none;font-size:.9rem;font-weight:500;border-left:3px solid transparent}
.pijar-drawer .drawer-item.active{color:#fb923c;border-left-color:#f97316;font-weight:700}
.pijar-drawer .drawer-footer{padding:12px 18px}
.pijar-sidebar :focus-visible,.pijar-bottom-nav :focus-visible,.pijar-drawer :focus-visible{outline:2px solid #fb923c;outline-offset:-3px}
.pijar-stok-dot{position:absolute;top:-2px;right:-2px;width:8px;height:8px;border-radius:50%;background:#dc2626;border:1.5px solid #0f2236;box-shadow:0 0 0 1px #dc262659}
@media(max-width:768px){.pijar-sidebar{display:none!important}.pijar-main,.main{margin-left:0!important;padding-bottom:calc(70px + env(safe-area-inset-bottom,0px))}.pijar-bottom-nav{display:flex}}
@media(min-width:769px){.pijar-bottom-nav,.pijar-drawer,.pijar-drawer-overlay{display:none!important}.pijar-main,.main{margin-left:224px}}
</style>`;
document.head.insertAdjacentHTML('beforeend',styles);
document.body.insertAdjacentHTML('afterbegin',sidebar);
document.body.insertAdjacentHTML('beforeend',mobile);
const logo=document.querySelector('#pijar-sidebar-el .brand-logo');
function fallback(){logo.style.display='none';logo.nextElementSibling.style.display='flex';}
logo.addEventListener('error',fallback);
if(logo.complete && logo.naturalWidth===0) fallback();
const name=user.nama_lengkap || user.nama || user.username || 'Pengguna';
['pijar-user','drawer-user'].forEach(prefix=>{
 const el=document.getElementById(prefix+'-name');el.textContent=name;el.title=name;
 document.getElementById(prefix+'-role').textContent=user.peran || '';
 document.getElementById(prefix+'-avatar').textContent=Array.from(name)[0].toUpperCase();
});
// Mempertahankan logout lokal; endpoint logout server tidak dipanggil di sini.
window.pijarLogout=function(){localStorage.removeItem('pijar_token');localStorage.removeItem('pijar_user');location.href=logoutHref;};
document.querySelectorAll('[data-pijar-logout]').forEach(b=>b.addEventListener('click',window.pijarLogout));
const drawer=document.getElementById('pijar-drawer');
const overlay=document.getElementById('pijar-drawer-overlay');
const more=document.getElementById('pijar-more');
const close=document.getElementById('pijar-drawer-close');
let previousFocus=null;
function closeDrawer(restore=true){const open=!drawer.hidden;drawer.hidden=true;overlay.classList.remove('show');more.setAttribute('aria-expanded','false');if(open && restore && previousFocus)previousFocus.focus();}
more.addEventListener('click',()=>{previousFocus=document.activeElement;drawer.hidden=false;overlay.classList.add('show');more.setAttribute('aria-expanded','true');close.focus();});
close.addEventListener('click',()=>closeDrawer());overlay.addEventListener('click',()=>closeDrawer());
document.addEventListener('keydown',e=>{
 if(drawer.hidden)return;
 if(e.key==='Escape'){e.preventDefault();closeDrawer();return;}
 if(e.key==='Tab'){
  const f=Array.from(drawer.querySelectorAll('a[href],button:not([disabled])'));
  const first=f[0],last=f[f.length-1];
  if(e.shiftKey && document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey && document.activeElement===last){e.preventDefault();first.focus();}
 }
});
window.addEventListener('resize',()=>{if(innerWidth>768)closeDrawer(false);});
function addStokBadge(count){
 if(!Number.isFinite(count)||count<=0)return;
 document.querySelectorAll('a[href$="index.html"]').forEach(a=>{
  if(a.querySelector('.pijar-stok-dot'))return;
  const icon=a.querySelector('svg');if(!icon)return;
  const wrap=document.createElement('span');wrap.style.position='relative';wrap.style.display='inline-flex';wrap.style.flexShrink='0';
  icon.parentNode.insertBefore(wrap,icon);wrap.appendChild(icon);
  const dot=document.createElement('span');dot.className='pijar-stok-dot';dot.title=`${count} komponen stok kritis`;wrap.appendChild(dot);
 });
}
async function loadStokBadge(){
 try{
  const token=localStorage.getItem('pijar_token');if(!token)return;
  const r=await fetch('https://api.pjujogja.id/api/dashboard/summary',{headers:{Authorization:'Bearer '+token},cache:'no-store'});
  if(!r.ok)return;
  const j=await r.json();addStokBadge(Number(j.data && j.data.stok_kritis));
 }catch(e){}
}
loadStokBadge();
})();
