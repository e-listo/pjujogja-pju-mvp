/**
 * PIJAR — Shared Sidebar
 * Inject sidebar + topbar ke semua halaman admin
 * Usage: <script src="js/sidebar.js" data-page="dashboard"></script>
 */
(function(){
  const PAGES = [
    { id:'dashboard',   label:'Dashboard',        href:'index.html',        icon:'M3 3h7v7H3zm11 0h7v7h-7zM3 14h7v7H3zm11 0h7v7h-7z' },
    { id:'aset',        label:'Data Aset',         href:'aset.html',         icon:'M12 2a7 7 0 1 1 0 14A7 7 0 0 1 12 2zm0 2a5 5 0 1 0 0 10A5 5 0 0 0 12 4zm0 2v4l3 2' },
    { id:'laporan',     label:'Laporan Kerusakan', href:'laporan.html',      icon:'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M16 13H8M16 17H8' },
    { id:'pemeliharaan',label:'Pemeliharaan',      href:'pemeliharaan.html', icon:'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z' },
    { id:'wilayah',     label:'Wilayah',           href:'wilayah.html',      icon:'M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15' },
    { id:'regu',        label:'Regu Lapangan',     href:'regu.html',         icon:'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 7a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75' },
  ];
  const LAPANGAN = [
    { id:'form-laporan',    label:'Form Laporan',    href:'lapangan/lapor.html', icon:'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
    { id:'form-penanganan', label:'Form Penanganan', href:'lapangan/form.html',  icon:'M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11' },
  ];

  const currentPage = (document.currentScript && document.currentScript.dataset.page) || '';

  function svgIcon(d){
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`;
  }

  function navItem(p){
    const active = (p.id === currentPage) ? ' active' : '';
    return `<a href="${p.href}" class="nav-item${active}" aria-current="${active?'page':'false'}">${svgIcon(p.icon)}<span>${p.label}</span></a>`;
  }

  const sidebarHTML = `
<aside class="pijar-sidebar" id="pijar-sidebar-el">
  <a href="index.html" class="sidebar-brand">
    <img
      src="/images/pijar_square.png"
      alt="Logo PIJAR"
      width="34" height="34"
      fetchpriority="high"
      style="width:34px;height:34px;object-fit:contain;flex-shrink:0;filter:drop-shadow(0 1px 6px rgba(249,115,22,.35))"
      onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
    />
    <span class="brand-fallback" style="display:none;width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#f97316,#facc15);align-items:center;justify-content:center;font-size:16px;flex-shrink:0">🔆</span>
    <div class="brand-text">
      <span class="brand-name">PIJAR</span>
      <span class="brand-sub">Sistem Manajemen Aset PJU<br>UPT PJU Kota Yogyakarta</span>
    </div>
  </a>

  <nav class="sidebar-nav" aria-label="Menu Utama">
    <div class="nav-group-label">Menu Utama</div>
    ${PAGES.map(navItem).join('')}
    <div class="nav-group-label" style="margin-top:10px">Lapangan</div>
    ${LAPANGAN.map(navItem).join('')}
  </nav>

  <div class="sidebar-user" id="pijar-user-box">
    <div class="user-avatar" id="pijar-user-avatar">A</div>
    <div class="user-info">
      <span class="user-name" id="pijar-user-name">—</span>
      <span class="user-role" id="pijar-user-role">—</span>
    </div>
    <button class="btn-logout" onclick="pijarLogout()" title="Keluar">&#x2715;</button>
  </div>
  <div class="sidebar-footer">Perwal Kota Yogyakarta No.&nbsp;50/2022</div>
</aside>`;

  const styles = `
<style id="pijar-sidebar-css">
.pijar-sidebar{
  position:fixed;top:0;left:0;width:224px;height:100vh;
  background:#0f2236;color:#e2e8f0;
  display:flex;flex-direction:column;z-index:200;
  border-right:1px solid rgba(255,255,255,0.07);
}
.sidebar-brand{
  display:flex;align-items:center;gap:10px;
  padding:14px 16px;border-bottom:1px solid rgba(255,255,255,0.08);
  text-decoration:none;flex-shrink:0;
}
.brand-text{display:flex;flex-direction:column;min-width:0;}
.brand-name{
  font-size:1.1rem;font-weight:900;color:#facc15;
  letter-spacing:.07em;line-height:1;
}
.brand-sub{
  font-size:.58rem;color:#475569;line-height:1.4;margin-top:2px;
  white-space:normal;
}
.sidebar-nav{flex:1;padding:8px 0;overflow-y:auto;overflow-x:hidden;}
.sidebar-nav::-webkit-scrollbar{width:3px;}
.sidebar-nav::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:3px;}
.nav-group-label{
  padding:8px 16px 3px;
  font-size:.6rem;font-weight:700;color:#334155;
  text-transform:uppercase;letter-spacing:.1em;
}
.nav-item{
  display:flex;align-items:center;gap:9px;
  padding:8px 16px;
  color:#64748b;text-decoration:none;font-size:.82rem;
  border-left:3px solid transparent;
  transition:background .15s,color .15s;
  white-space:nowrap;
}
.nav-item svg{
  width:16px;height:16px;flex-shrink:0;
  stroke:#64748b;transition:stroke .15s;
}
.nav-item:hover{
  background:rgba(255,255,255,0.05);
  color:#e2e8f0;
  border-left-color:rgba(249,115,22,.4);
}
.nav-item:hover svg{stroke:#e2e8f0;}
.nav-item.active{
  background:rgba(249,115,22,.1);
  color:#fff;font-weight:600;
  border-left-color:#f97316;
}
.nav-item.active svg{stroke:#f97316;}
.sidebar-user{
  display:flex;align-items:center;gap:9px;
  padding:12px 14px;
  border-top:1px solid rgba(255,255,255,0.07);
  min-height:58px;
}
.user-avatar{
  width:30px;height:30px;border-radius:50%;
  background:linear-gradient(135deg,#1a56db,#1e3a5f);
  color:#fff;font-size:.82rem;font-weight:700;
  display:flex;align-items:center;justify-content:center;
  flex-shrink:0;border:1.5px solid rgba(249,115,22,.4);
}
.user-info{flex:1;min-width:0;overflow:hidden;}
.user-name{
  display:block;font-size:.78rem;font-weight:600;
  color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}
.user-role{
  display:block;font-size:.66rem;color:#475569;
  margin-top:1px;text-transform:capitalize;
}
.btn-logout{
  background:none;border:none;color:#334155;
  font-size:.9rem;cursor:pointer;padding:4px;
  border-radius:4px;transition:color .15s;
  flex-shrink:0;
}
.btn-logout:hover{color:#f87171;}
.sidebar-footer{
  padding:7px 14px;
  font-size:.58rem;color:#1e3a5f;
  border-top:1px solid rgba(255,255,255,0.04);
}
@media(max-width:768px){
  .pijar-sidebar{display:none;}
  .pijar-main{margin-left:0!important;}
}
</style>`;

  document.head.insertAdjacentHTML('beforeend', styles);
  document.body.insertAdjacentHTML('afterbegin', sidebarHTML);

  const style = document.createElement('style');
  style.textContent = '.pijar-main,.main{margin-left:224px;}';
  document.head.appendChild(style);

  function fillUser(){
    try{
      const raw = localStorage.getItem('pijar_user');
      if(!raw) return;
      const u = JSON.parse(raw);
      const name = u.nama_lengkap || u.nama || u.username || '?';
      const role = u.peran || u.role || '';
      const el = document.getElementById('pijar-user-name');
      const er = document.getElementById('pijar-user-role');
      const ea = document.getElementById('pijar-user-avatar');
      if(el) el.textContent = name;
      if(er) er.textContent = role;
      if(ea) ea.textContent = name.charAt(0).toUpperCase();
    }catch(e){}
  }

  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', fillUser);
  } else {
    fillUser();
  }

  window.pijarLogout = function(){
    localStorage.removeItem('pijar_token');
    localStorage.removeItem('pijar_user');
    window.location.href = 'login.html';
  };

})();
