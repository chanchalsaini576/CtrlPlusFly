// hud.js - ye woh chhota telemetry box hai jo har page ke corner me dikhta hai
// bas random numbers generate karke ALT/SPD/GPS/SIG dikha raha hai, thoda alive feel dene ke liye
(function(){
  var mount = document.getElementById('global-hud');
  if(!mount) return;

  mount.innerHTML =
    '<span class="hud-title">LINK ACTIVE // TLM</span>' +
    '<div class="row"><span>ALT</span><span id="hud-alt">--</span></div>' +
    '<div class="row"><span>SPD</span><span id="hud-spd">--</span></div>' +
    '<div class="row"><span>GPS</span><span id="hud-gps">--</span></div>' +
    '<div class="row"><span>SIG</span><span id="hud-sig">--</span></div>';

  var alt = 0, spd = 0, lat = 26.9124, lon = 75.7873; // Jaipur, home base
  var altEl = document.getElementById('hud-alt');
  var spdEl = document.getElementById('hud-spd');
  var gpsEl = document.getElementById('hud-gps');
  var sigEl = document.getElementById('hud-sig');

  function tick(){
    alt = Math.max(0, alt + (Math.random()-0.45) * 6);
    spd = Math.max(0, 12 + Math.sin(Date.now()/1400) * 8 + Math.random()*2);
    lat += (Math.random()-0.5) * 0.0006;
    lon += (Math.random()-0.5) * 0.0006;
    var sig = 78 + Math.round(Math.sin(Date.now()/900) * 14);

    altEl.textContent = alt.toFixed(1) + ' m';
    spdEl.textContent = spd.toFixed(1) + ' km/h';
    gpsEl.textContent = lat.toFixed(4) + ', ' + lon.toFixed(4);
    sigEl.textContent = sig + '%';
  }
  tick();
  setInterval(tick, 1400);
})();
