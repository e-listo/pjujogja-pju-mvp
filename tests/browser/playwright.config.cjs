const {defineConfig} = require('@playwright/test');
module.exports=defineConfig({
 testDir: __dirname,
 testMatch: 'bulk-import.spec.cjs',
 workers: 1,
 retries: 0,
 timeout: 30000,
 reporter: [['list'],['html',{outputFolder:'playwright-report',open:'never'}]],
 use: {baseURL:'http://127.0.0.1:5000',headless:true,screenshot:'only-on-failure',trace:'retain-on-failure'},
 projects: [
  {name:'desktop',use:{browserName:'chromium',viewport:{width:1366,height:900}}},
  {name:'tablet',use:{browserName:'chromium',viewport:{width:800,height:1280}}},
  {name:'phone',use:{browserName:'chromium',viewport:{width:390,height:844}}}
 ]
});
