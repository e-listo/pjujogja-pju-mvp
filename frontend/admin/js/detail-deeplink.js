// Auto-buka modal detail aset dari deep-link ?detail=<id>
// Dipakai oleh aset.html — panggil setelah script utama & fungsi bukaDetail() siap.
(function(){
  function jalankan(){
    var id = new URLSearchParams(window.location.search).get('detail');
    if(!id) return;
    var coba = 0;
    var timer = setInterval(function(){
      coba++;
      if(typeof window.bukaDetail === 'function'){
        clearInterval(timer);
        window.bukaDetail(parseInt(id, 10));
      } else if(coba > 20){
        clearInterval(timer);
      }
    }, 200);
  }
  if(document.readyState === 'complete' || document.readyState === 'interactive'){
    jalankan();
  } else {
    document.addEventListener('DOMContentLoaded', jalankan);
  }
})();

// Muat modal bulk import setelah halaman aset selesai diinisialisasi.
(function(){
  var sumber = new URL('aset-bulk.js?v=20261007b', document.currentScript.src).href;
  function muatBulk(){
    if(!document.querySelector('.topbar-actions')) return;
    if(document.querySelector('script[data-pijar-bulk]')) return;
    var script = document.createElement('script');
    script.src = sumber;
    script.dataset.pijarBulk = '1';
    document.body.appendChild(script);
  }
  if(document.readyState === 'loading'){
    document.addEventListener('DOMContentLoaded', muatBulk);
  } else {
    muatBulk();
  }
})();
