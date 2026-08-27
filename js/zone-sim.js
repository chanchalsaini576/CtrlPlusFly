// zone-sim.js - simulator zone pages (desert/city/arctic/ocean) sab isi file ko use karte hai
// query string se level/drone/speed/ceiling padhta hai, HUD stats update karta hai,
// gate clicks handle karta hai aur camera switch karta hai (FPV/chase/topdown/orbit)
(function(){
  var params = new URLSearchParams(window.location.search);
  var level = parseInt(params.get('level') || '1', 10);
  var droneName = params.get('drone') || 'Sparrow-X';
  var topSpeed = parseFloat(params.get('top') || '55');
  var ceiling = parseFloat(params.get('ceil') || '500');

  var ALT_RANGES = { 1:[40,90], 2:[120,220], 3:[260,420] };
  var range = ALT_RANGES[level] || ALT_RANGES[1];
  var cfg = window.ZONE_CONFIG || { name:'Zone', code:'ZN', gates:3, distanceKm:2.4 };

  // ---- badges ----
  var zoneNameEl = document.getElementById('sim-zone-name');
  var droneNameEl = document.getElementById('sim-drone-name');
  var lvlEl = document.getElementById('sim-level');
  if(zoneNameEl) zoneNameEl.textContent = cfg.name;
  if(droneNameEl) droneNameEl.textContent = droneName;
  if(lvlEl) lvlEl.textContent = 'LEVEL ' + level;

  // ---- live stats ----
  var altEl = document.getElementById('stat-alt');
  var spdEl = document.getElementById('stat-spd');
  var distEl = document.getElementById('stat-dist');
  var gatesEl = document.getElementById('stat-gates');
  var headingEl = document.getElementById('stat-heading');

  var totalGates = cfg.gates;
  var cleared = 0;
  var distanceCovered = 0;
  var heading = 0;

  function fmt(n, d){ return n.toFixed(d===undefined?1:d); }

  function tick(){
    var alt = range[0] + Math.random()*(range[1]-range[0]);
    var spd = Math.max(4, topSpeed * (0.55 + Math.random()*0.4));
    distanceCovered = Math.min(cfg.distanceKm, distanceCovered + spd/3600*1.4);
    heading = (heading + Math.random()*14 - 7 + 360) % 360;

    if(altEl) altEl.textContent = fmt(alt,0) + ' m';
    if(spdEl) spdEl.textContent = fmt(spd,1) + ' km/h';
    if(distEl) distEl.textContent = fmt(cfg.distanceKm - distanceCovered,2) + ' km';
    if(headingEl) headingEl.textContent = fmt(heading,0) + '°';
    if(gatesEl) gatesEl.textContent = cleared + ' / ' + totalGates;
  }
  tick();
  setInterval(tick, 1600);

  // ---- ceiling readout (static, from chosen airframe) ----
  var ceilEl = document.getElementById('stat-ceiling');
  if(ceilEl) ceilEl.textContent = ceiling + ' m';

  // ---- gate clearing ----
  var banner = document.getElementById('mission-banner');
  document.querySelectorAll('.gate').forEach(function(g){
    g.addEventListener('click', function(){
      if(g.classList.contains('cleared')) return;
      g.classList.add('cleared');
      cleared++;
      if(gatesEl) gatesEl.textContent = cleared + ' / ' + totalGates;
      if(cleared >= totalGates && banner){
        banner.textContent = 'ALL GATES CLEARED — ' + cfg.name.toUpperCase() + ' RUN COMPLETE';
        banner.classList.add('show');
      }
    });
  });

  // ---- camera shift ----
  var views = ['FPV', 'CHASE CAM', 'TOP-DOWN', 'ORBIT'];
  var viewClasses = ['cam-fpv','cam-chase','cam-topdown','cam-orbit'];
  var viewIdx = 0;
  var stage = document.getElementById('sim-stage');
  var camBtn = document.getElementById('cam-shift-btn');
  var camLabel = document.getElementById('cam-label');

  function applyView(){
    if(!stage) return;
    viewClasses.forEach(function(c){ stage.classList.remove(c); });
    stage.classList.add(viewClasses[viewIdx]);
    if(camLabel) camLabel.textContent = views[viewIdx];
  }
  applyView();
  if(camBtn){
    camBtn.addEventListener('click', function(){
      viewIdx = (viewIdx + 1) % views.length;
      applyView();
    });
  }
})();
