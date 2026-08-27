// telemetry-console.js - telemetry.html ke "analysis console" wale part ka JS
// backend ke api routes ko fetch karta hai (generate/encrypt/decrypt/upload) aur result table me dikhata hai
(function(){
  var logBox = document.getElementById('console-log');
  var summary = document.getElementById('result-summary');
  var table = document.getElementById('result-table');
  var tbody = document.getElementById('result-table-body');
  var rsTotal = document.getElementById('rs-total');
  var rsValid = document.getElementById('rs-valid');
  var rsFlagged = document.getElementById('rs-flagged');

  if(!logBox) return; // this script only runs on telemetry.html

  function log(msg, kind){
    var line = document.createElement('div');
    line.className = 'line' + (kind ? ' ' + kind : '');
    line.textContent = '> ' + msg;
    logBox.appendChild(line);
    logBox.scrollTop = logBox.scrollHeight;
  }

  function showReport(report){
    if(!report) return;
    summary.style.display = 'flex';
    rsTotal.textContent = report.total_records;
    rsValid.textContent = report.valid_records;
    rsFlagged.textContent = report.flagged_records;
  }

  function showRecords(records){
    if(!records || !records.length) return;
    table.style.display = 'table';
    tbody.innerHTML = '';
    records.slice(0, 25).forEach(function(r){
      var tr = document.createElement('tr');
      ['timestamp','lat','lon','alt_m','speed_kmh','heading','battery_v','sats'].forEach(function(k){
        var td = document.createElement('td');
        td.textContent = (r[k] === null || r[k] === undefined) ? '—' : r[k];
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    if(records.length > 25) log('showing first 25 of ' + records.length + ' records (full set is in the CSV/KML export)');
  }

  async function postJSON(url, body){
    var res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {})
    });
    var data = await res.json().catch(function(){ return {}; });
    if(!res.ok) throw new Error(data.error || ('request failed (' + res.status + ')'));
    return data;
  }

  async function postForm(url, formData){
    var res = await fetch(url, { method: 'POST', body: formData });
    var data = await res.json().catch(function(){ return {}; });
    if(!res.ok) throw new Error(data.error || ('request failed (' + res.status + ')'));
    return data;
  }

  // ---- Step 1a: generate sample flight ----
  var btnGenerate = document.getElementById('btn-generate');
  if(btnGenerate) btnGenerate.addEventListener('click', async function(){
    var zone = document.getElementById('gen-zone').value;
    var level = document.getElementById('gen-level').value;
    var duration = document.getElementById('gen-duration').value;
    log('generating ' + duration + 's sample flight over ' + zone + ' (level ' + level + ')…');
    try{
      var data = await postJSON('/api/telemetry/generate', { zone: zone, level: level, duration: duration });
      log(data.count + ' telemetry records generated', 'ok');
      showReport({ total_records: data.count, valid_records: data.count, flagged_records: 0 });
      showRecords(data.records);
    }catch(e){
      log('backend not reachable — run "python backend/app.py" first (' + e.message + ')', 'err');
    }
  });

  // ---- Step 1b: upload user's own CSV ----
  var btnUploadCsv = document.getElementById('btn-upload-csv');
  if(btnUploadCsv) btnUploadCsv.addEventListener('click', async function(){
    var fileInput = document.getElementById('upload-csv');
    if(!fileInput.files.length){ log('choose a CSV file first', 'err'); return; }
    var fd = new FormData();
    fd.append('file', fileInput.files[0]);
    log('uploading ' + fileInput.files[0].name + ' for parsing + validation…');
    try{
      var data = await postForm('/api/telemetry/upload-csv', fd);
      log('parsed ' + data.report.total_records + ' rows, ' + data.report.flagged_records + ' flagged', 'ok');
      showReport(data.report);
      showRecords(data.records);
    }catch(e){
      log('upload failed (' + e.message + ')', 'err');
    }
  });

  // ---- Step 2a: encrypt current flight ----
  var btnEncrypt = document.getElementById('btn-encrypt');
  if(btnEncrypt) btnEncrypt.addEventListener('click', async function(){
    var password = document.getElementById('enc-pass').value;
    log('encrypting current flight record…');
    try{
      var data = await postJSON('/api/telemetry/encrypt', { password: password });
      log('encrypted — ' + data.size_bytes + ' bytes. Use "Download .enc" to save it.', 'ok');
    }catch(e){
      log('encryption failed (' + e.message + ')', 'err');
    }
  });

  // ---- Step 2b: decrypt + validate ----
  var btnDecrypt = document.getElementById('btn-decrypt');
  if(btnDecrypt) btnDecrypt.addEventListener('click', async function(){
    var password = document.getElementById('dec-pass').value;
    var fileInput = document.getElementById('dec-file');
    try{
      var data;
      if(fileInput.files.length){
        var fd = new FormData();
        fd.append('file', fileInput.files[0]);
        fd.append('password', password);
        log('decrypting uploaded file ' + fileInput.files[0].name + '…');
        data = await postForm('/api/telemetry/validate', fd);
      } else {
        log('decrypting the in-memory encrypted flight…');
        data = await postJSON('/api/telemetry/validate', { password: password });
      }
      log('decrypted + validated — ' + data.report.valid_records + '/' + data.report.total_records + ' records valid', 'ok');
      showReport(data.report);
      showRecords(data.records);
    }catch(e){
      log('decrypt/validate failed (' + e.message + ')', 'err');
    }
  });
})();
