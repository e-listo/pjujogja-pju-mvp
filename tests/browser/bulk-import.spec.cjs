const {test,expect} = require('@playwright/test');
const BASE='http://127.0.0.1:5000';
const CODE='PJUP-UH2-26-001';
const HEADER='kode_aset,kode_kategori,kode_wilayah,sektor,tahun_pemasangan,alamat,lat,lng,kategori_jalan,sub_kategori_lainnya,jenis_tiang,tinggi_meter,status';
const csv=(lat='-7.8')=>Buffer.from(HEADER+'\n'+CODE+',PJUP,UH2,Sektor 1,2026,Lokasi uji,'+lat+',110.37,Jalan Kota,,Besi,8,Menyala\n');
let auth;
test.beforeEach(async({page,request},info)=>{
 const reset=await request.post(BASE+'/__test__/reset',{headers:{'X-Test-Reset':'ci-only'}});expect(reset.ok()).toBeTruthy();
 const role=info.title.includes('teknisi')?'teknisi':'admin';
 const login=await request.post(BASE+'/api/auth/login',{data:{username:role,password:'ci-only'}});expect(login.ok()).toBeTruthy();
 const data=await login.json();auth={Authorization:'Bearer '+data.token};
 await page.context().addInitScript(data=>{localStorage.setItem('pijar_token',data.token);localStorage.setItem('pijar_user',JSON.stringify(data.pengguna));},data);
 await page.context().route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname==='api.pjujogja.id'){
   const response=await route.fetch({url:BASE+url.pathname+url.search,maxRedirects:0});await route.fulfill({response});
  }else if(url.hostname==='127.0.0.1')await route.continue();
  else await route.abort();
 });
 await page.goto('/test-ui/aset.html');
});
async function open(page){await page.locator('#bulk-import-open').click();await expect(page.locator('#modal-bulk')).toBeVisible();}
async function upload(page,lat='-7.8'){await page.locator('#bulk-file').setInputFiles({name:'uji.csv',mimeType:'text/csv',buffer:csv(lat)});}
async function preview(page){await page.locator('#bulk-preview').click();await expect(page.locator('#bulk-save')).toBeEnabled();}
async function count(request){const r=await request.get(BASE+'/api/aset?q='+CODE,{headers:auth});expect(r.ok()).toBeTruthy();return (await r.json()).data.filter(x=>x.kode_aset===CODE).length;}

test('modal terbuka',async({page})=>{await open(page);await expect(page.locator('#bulk-save')).toBeDisabled();await expect(page.locator('#bulk-preview')).toBeDisabled();});
test('modal tertutup dengan tombol Tutup',async({page})=>{await open(page);await page.locator('#bulk-close').click();await expect(page.locator('#modal-bulk')).toBeHidden();});
test('unduh template Excel',async({page})=>{await open(page);const pending=page.waitForEvent('download');await page.locator('#bulk-xlsx').click();const d=await pending;expect(d.suggestedFilename()).toMatch(/\.xlsx$/);expect(await d.failure()).toBeNull();});
test('template CSV dinonaktifkan sementara',async({page})=>{await open(page);await expect(page.locator('#bulk-csv')).toHaveAttribute('aria-disabled','true');await page.locator('#bulk-csv').click();await expect(page.locator('#bulk-status')).toContainText('CSV sementara dinonaktifkan');});
test('preview dan simpan',async({page,request})=>{await open(page);await upload(page);await preview(page);await expect(page.locator('#bulk-result table')).toHaveCount(1);expect(await count(request)).toBe(0);await page.locator('#bulk-save').click();await expect(page.locator('#modal-konfirmasi')).toBeVisible();await page.locator('#konfirm-ok').click();await expect(page.locator('#bulk-status')).toContainText('Berhasil: 1 aset');expect(await count(request)).toBe(1);});
test('ganti berkas membatalkan preview',async({page})=>{await open(page);await upload(page);await preview(page);await upload(page,'-7.81');await expect(page.locator('#bulk-save')).toBeDisabled();await expect(page.locator('#bulk-result table')).toHaveCount(0);});
test('koordinat salah ditolak',async({page,request})=>{await open(page);await upload(page,'100');await page.locator('#bulk-preview').click();await expect(page.locator('#bulk-status')).toContainText('Data_Aset baris');await expect(page.locator('#bulk-save')).toBeDisabled();expect(await count(request)).toBe(0);});
test('batal konfirmasi tidak menyimpan',async({page,request})=>{await open(page);await upload(page);await preview(page);await page.locator('#bulk-save').click();await expect(page.locator('#modal-konfirmasi')).toBeVisible();await page.locator('#konfirm-batal').click();await expect(page.locator('#modal-konfirmasi')).toBeHidden();expect(await count(request)).toBe(0);await expect(page.locator('#bulk-save')).toBeEnabled();});
test('teknisi tidak melihat tombol',async({page})=>{await expect(page.locator('script[data-pijar-bulk]')).toHaveCount(1);await page.waitForFunction(()=>performance.getEntriesByType('resource').some(r=>r.name.includes('/aset-bulk.js')));await page.evaluate(()=>new Promise(resolve=>setTimeout(resolve,100)));await expect(page.locator('#bulk-import-open')).toHaveCount(0);});
