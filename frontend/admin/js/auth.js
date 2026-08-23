/**
 * auth.js — Guard autentikasi untuk semua halaman admin PIJAR
 * Include di setiap halaman admin: <script src="js/auth.js"></script>
 * Letakkan di atas semua script lain.
 */
(function () {
  const API = 'https://api.pjujogja.id';
  const LOGIN_PAGE = '/login.html';

  const token = localStorage.getItem('pijar_token');

  // Tidak ada token → redirect ke login
  if (!token) {
    window.location.href = LOGIN_PAGE;
    return;
  }

  // Cek expire dari JWT payload (tanpa verifikasi signature)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (payload.exp * 1000 < Date.now()) {
      localStorage.removeItem('pijar_token');
      localStorage.removeItem('pijar_user');
      window.location.href = LOGIN_PAGE;
      return;
    }
    // Simpan user ke window supaya bisa dipakai halaman
    window.PIJAR_USER = payload;
  } catch (e) {
    localStorage.removeItem('pijar_token');
    window.location.href = LOGIN_PAGE;
    return;
  }

  // Helper global: fetch dengan token otomatis
  window.apiFetch = function (url, options = {}) {
    const headers = Object.assign({ 'Authorization': 'Bearer ' + token }, options.headers || {});
    return fetch(url, Object.assign({}, options, { headers }));
  };

  // Helper global: logout
  window.pijarLogout = function () {
    localStorage.removeItem('pijar_token');
    localStorage.removeItem('pijar_user');
    window.location.href = LOGIN_PAGE;
  };

  // Render nama user di elemen #user-info jika ada
  document.addEventListener('DOMContentLoaded', function () {
    const el = document.getElementById('user-info');
    if (el && window.PIJAR_USER) {
      el.innerHTML = `
        <span style="font-size:0.82rem;color:#cbd5e1">
          👤 ${window.PIJAR_USER.nama}
          <span style="font-size:0.72rem;color:#64748b;margin-left:4px">(${window.PIJAR_USER.peran})</span>
        </span>
        <button onclick="pijarLogout()" style="margin-left:10px;padding:3px 10px;border-radius:5px;border:1px solid #475569;background:transparent;color:#cbd5e1;font-size:0.78rem;cursor:pointer">Keluar</button>
      `;
    }
  });
})();
