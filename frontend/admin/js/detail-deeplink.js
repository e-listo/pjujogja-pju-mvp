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
