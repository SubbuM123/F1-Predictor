(async function(){

"use strict";
// @TODO completed race needs to read from a new file with the current standings, not all predictions which only holds the knn model dat
const [allPredictions, metrics] = await Promise.all([
    fetch("./json/all_predictions.json?v=" + new Date().getTime()).then(r => r.json()),
    fetch("./json/metrics.json").then(r => r.json()),
    // fetch("./json/all_predictions.json?v=" + new Date().getTime()).then(r => r.json()).then(data => data["completed race"])
]);

const completedRace = Math.max(...Object.keys(allPredictions).map(Number));

// console.log("Completed race:", completedRace);

  const racesThisSeason = 22;
  const maxRacesLeft = racesThisSeason - 5;

  const TEAMS = [
    "Red Bull Racing", "Aston Martin Racing", "Cadillac F1 Team", "Haas F1 Team",
    "Racing Bulls", "Mercedes", "Ferrari", "McLaren", "Alpine", "Williams", "Audi"
  ].sort((a,b) => b.length - a.length);

  const DRIVER_TEAMS = {
  "A. Antonelli": "Mercedes",
  "G. Russell": "Mercedes",
  "L. Hamilton": "Ferrari",
  "C. Leclerc": "Ferrari",
  "L. Norris": "McLaren",
  "O. Piastri": "McLaren",
  "M. Verstappen": "Red Bull Racing",
  "I. Hadjar": "Red Bull Racing",
  "P. Gasly": "Alpine",
  "F. Colapinto": "Alpine",
  "L. Lawson": "Racing Bulls",
  "A. Lindblad": "Racing Bulls",
  "O. Bearman": "Haas F1 Team",
  "E. Ocon": "Haas F1 Team",
  "A. Albon": "Williams",
  "C. Sainz": "Williams",
  "F. Alonso": "Aston Martin Racing",
  "L. Stroll": "Aston Martin Racing",
  "G. Bortoleto": "Audi",
  "N. Hulkenberg": "Audi",
  "V. Bottas": "Cadillac F1 Team",
  "S. Perez": "Cadillac F1 Team"
  };

  const TEAM_COLORS = {
    "Mercedes": "#27F4C4",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Red Bull Racing": "#3671C6",
    "Alpine": "#2293D1",
    "Williams": "#64C4FF",
    "Racing Bulls": "#6C98FF",
    "Haas F1 Team": "#B6BABD",
    "Audi": "#BB0A30",
    "Cadillac F1 Team": "#C9A227",
    "Aston Martin Racing": "#229971"
  };

  // function parseKey(key){
  //   const team = TEAMS.find(t => key.endsWith(t));
  //   const name = team ? key.slice(0, key.length - team.length) : key;
  //   return { name, team: team || "Unknown" };
  // }

  function parseKey(name) {
  return {
    name,
    team: DRIVER_TEAMS[name] || "Unknown"
    };
  }
  const metadataKeys = new Set(["completed race", "point total"]);
  // const drivers = Object.keys(rawDrivers)
  // .filter(key => !metadataKeys.has(key))
  // .map(key => {
  //   const { name, team } = parseKey(key);
  //   const d = rawDrivers[key];
  //   return {
  //     name, team,
  //     first: d["1st"] || 0,
  //     podium: d["Podium"] || 0,
  //     top5: d["Top 5"] || 0,
  //     top10: d["Top 10"] || 0,
  //     points: d["points"] || 0
  //   };
  // }).sort((a,b) => b.points - a.points);

  let drivers = buildDrivers(completedRace);

  function buildDrivers(completedRace) {
    //console.log(racesLeft, racesThisSeason - racesLeft, allPredictions);
    // const racesLeft = racesThisSeason - completedRace;
    const rawDrivers = allPredictions[completedRace];

    if (!rawDrivers)
        return [];

    return Object.keys(rawDrivers)
        .filter(key => !metadataKeys.has(key))
        .map(key => {

            const { name, team } = parseKey(key);
            const d = rawDrivers[key];

            return {
                name,
                team,
                first: d["1st"] || 0,
                podium: d["Podium"] || 0,
                top5: d["Top 5"] || 0,
                top10: d["Top 10"] || 0,
                points: d["points"] || 0
            };

        })
        .sort((a,b) => b.points-a.points);
  }


  const maxPoints = Math.max(...drivers.map(d => d.points));
  document.getElementById('driverCount').textContent = drivers.length;

  function raceKey(n){ return "Races Left: " + n; }
  // function metricAt(name, racesLeft){ return metrics[name][raceKey(racesLeft)]; }
  function metricAt(name, racesLeft){
    const key = raceKey(racesLeft);
    const val = metrics?.[name]?.[key];

    if (val == null) {
      console.warn("Missing metric:", name, key, metrics);
    }

    return val;
  }
  function pct(v, decimals){ return v.toFixed(decimals === undefined ? 2 : decimals) + "%"; }

  // ---------- ticks ----------
  const ticksEl = document.getElementById('ticks');
  const shownTicks = [maxRacesLeft, 15,13,11,9,7,5,3,1];
  for(let n = maxRacesLeft; n >= 1; n--){
    const s = document.createElement('span');
    s.textContent = shownTicks.includes(n) ? n : "";
    if(shownTicks.includes(n)) s.classList.add('on');
    ticksEl.appendChild(s);
  }

  // ---------- driver rows ----------
  const rowsEl = document.getElementById('rows');
  const probFields = [
    { key: 'first', cat: 'first', digits: 2 },
    { key: 'podium', cat: 'podium', digits: 2 },
    { key: 'top5', cat: 'top5', digits: 2 },
    { key: 'top10', cat: 'top10', digits: 2 }
  ];

  // ---------- tooltip ----------
  const tooltip = document.getElementById('tooltip');
  let racesLeft = 22 - completedRace;
  //let racesLeft = 14;
  const CATEGORY_CONFIG = {
    first: {
      label: 'P1 Finish',
      valueKey: 'first',
      lines: [
        { metric: 'Champion Correct', desc: "of the time, this model's #1 pick went on to become champion, at this stage of the season." }
      ]
    },
    podium: {
      label: 'Podium Finish',
      valueKey: 'podium',
      lines: [
        { metric: 'T3 Correct', desc: 'of the time, the model correctly had a driver finishing in the top 3, at this stage in the season.' },
        { metric: 'T3 Order Correct', desc: 'of the time, it nailed the exact podium order, at this stage in the season.' }
      ]
    },
    top5: {
      label: 'Top 5 Finish',
      valueKey: 'top5',
      lines: [
        { metric: 'T5 Correct', desc: 'of the time, the model correctly had a driver in the top 5, at this stage in the season.' },
        { metric: 'T5 Order Correct', desc: 'of the time, it nailed the exact top-5 order, at this stage in the season.' }
      ]
    },
    top10: {
      label: 'Top 10 Finish',
      valueKey: 'top10',
      lines: [
        { metric: 'T10 Correct', desc: 'of the time, the model correctly had a driver in the top 10, at this stage in the season.' },
        { metric: 'T10 Order Correct', desc: 'of the time, it nailed the exact top-10 order, at this stage in the season.' }
      ]
    }
  };

  function showTooltip(e, driver, cat){
    let html = '';
    if(cat === 'points'){
      const r2 = metricAt('R2', racesLeft);
      // const r2 = racesLeft > 13
      // ? metricAt('R2', racesLeft)
      // : metricAt('R2', 13);
      const mae = metricAt('Mean Absolute Error', racesLeft);
      const mare = metricAt('MARE', racesLeft);
      html = `
        <div class="tt-head"><span class="tt-driver">${driver.name}</span><span class="tt-cat">Season Points</span></div>
        <div class="tt-big">${Math.round(driver.points)}</div>
        <div class="tt-big-label">projected points, ${driver.team}</div>
        <hr class="tt-divider">
        <div class="tt-context-label">Points model, ${racesLeft} races left</div>
        <div class="tt-metric-row"><span class="tt-metric-val">${r2.toFixed(2)}</span><span class="tt-metric-desc">R&sup2; fit against final points &mdash; 1.0 is a perfect match.</span></div>
        <div class="tt-metric-row"><span class="tt-metric-val">&plusmn;${mae.toFixed(1)}</span><span class="tt-metric-desc">average points of offset per driver at this stage.</span></div>
        <div class="tt-metric-row"><span class="tt-metric-val">${mare.toFixed(2)}</span><span class="tt-metric-desc">average position offset across the grid.</span></div>
      `;
    } else {
      const cfg = CATEGORY_CONFIG[cat];
      const val = driver[cfg.valueKey];
      html = `
        <div class="tt-head"><span class="tt-driver">${driver.name}</span><span class="tt-cat">${cfg.label}</span></div>
        <div class="tt-big">${val < 0.005 ? '<0.01' : val.toFixed(val < 1 ? 2 : 1)}%</div>
        <div class="tt-big-label">current model probability</div>
        <hr class="tt-divider">
        <div class="tt-context-label">Track record, ${racesLeft} races left</div>
        ${cfg.lines.map(l => {
          const v = metricAt(l.metric, racesLeft) * 100;
          return `<div class="tt-metric-row"><span class="tt-metric-val">${v < 0.1 ? v.toFixed(2) : v.toFixed(1)}%</span><span class="tt-metric-desc">${l.desc}</span></div>`;
        }).join('')}
      `;
    }
    tooltip.innerHTML = html;
    tooltip.classList.add('visible');
    positionTooltip(e);
  }

  function positionTooltip(e){
    const offset = 18;
    let x = e.clientX + offset;
    let y = e.clientY + offset;
    const rect = tooltip.getBoundingClientRect();
    const w = rect.width || 262;
    const h = rect.height || 160;
    if(x + w > window.innerWidth - 12) x = e.clientX - w - offset;
    if(y + h > window.innerHeight - 12) y = e.clientY - h - offset;
    tooltip.style.left = Math.max(8,x) + 'px';
    tooltip.style.top = Math.max(8,y) + 'px';
  }

  function hideTooltip(){
    tooltip.classList.remove('visible');
  }

  // ---------- stat tiles ----------
  const tileDefs = [
    { key: 'Champion Correct', label: 'Champion Pick Accuracy', fmt: v => (v*100).toFixed(1)+'%', isPct:true },
    { key: 'T3 Correct', label: 'Podium Set Accuracy', fmt: v => (v*100).toFixed(1)+'%', isPct:true },
    { key: 'T5 Correct', label: 'Top 5 Set Accuracy', fmt: v => (v*100).toFixed(1)+'%', isPct:true },
    { key: 'T10 Correct', label: 'Top 10 Set Accuracy', fmt: v => (v*100).toFixed(1)+'%', isPct:true },
    { key: 'MARE', label: 'Average Position Offset', fmt: v => v.toFixed(3), isPct:false }
  ];
  const tilesEl = document.getElementById('tiles');
  tileDefs.forEach(t => {
    const tile = document.createElement('div');
    tile.className = 'tile';
    tile.dataset.key = t.key;
    tile.innerHTML = `
      <div class="tile-label">${t.label}</div>
      <div class="tile-value"><span class="tv"></span></div>
      <div class="tile-delta"><span class="td"></span></div>
    `;
    tilesEl.appendChild(tile);
  });

  function renderTiles(){
    // limit this upto the latest completed race -- fill past with disclaimer that data will fill in soon, so need a max value
    tileDefs.forEach(t => {
      const tile = tilesEl.querySelector(`[data-key="${t.key}"]`);
      const val = metricAt(t.key, racesLeft);
      const base = metricAt(t.key, maxRacesLeft);
      tile.querySelector('.tv').textContent = t.fmt(val);
      const deltaEl = tile.querySelector('.td');
      const diff = t.isPct ? (val - base) * 100 : (val - base);
      if(racesLeft === maxRacesLeft){
        deltaEl.innerHTML = `<span class="base">baseline &mdash; season start</span>`;
        deltaEl.className = 'tile-delta';
      } else {
        const sign = diff >= 0 ? '+' : '';
        const cls = diff >= 0 ? 'up' : 'down';
        //deltaEl.className = 'tile-delta ' + cls;
        //deltaEl.innerHTML = `${sign}${diff.toFixed(t.isPct ? 1 : 3)}${t.isPct ? 'pp' : ''}<span class="base">vs. 18 left</span>`;
      }
    });
  }

  function currentPrediction() {
    return allPredictions[racesLeft];
  }


  // ---------- scrubber wiring ----------
  const scrubber = document.getElementById('scrubber');
  const racesLeftNum = document.getElementById('racesLeftNum');
  const hintNum = document.getElementById('hintNum');
  const trackFill = document.getElementById('trackFill');

//   function renderScrubber(){
//     racesLeftNum.textContent = racesLeft;
//     hintNum.textContent = racesLeft;
//     const pctFill = ((18-racesLeft)/17)*100;
//     // const pctFill = ((18 - racesLeft) / 17) * 100;
//     // const pctFill = ((sliderValue-1)/17)*100;
//     trackFill.style.width = pctFill + '%';
//   }

    function renderScrubber(){

        // Keep the slider thumb synchronized
        scrubber.value = (maxRacesLeft + 1) - racesLeft;
        //console.log("Scrubber value:", scrubber.value)

        racesLeftNum.textContent = racesLeft;
        hintNum.textContent = racesLeft;

        const pctFill = ((maxRacesLeft-racesLeft)/(maxRacesLeft-1))*100;
        trackFill.style.width = pctFill + '%';
    }

    function renderDriverRows() {



      rowsEl.innerHTML = "";

        drivers.forEach((d, i) => {
          const row = document.createElement('div');
          row.className = 'row-grid driver-row';

          const teamColor = TEAM_COLORS[d.team] || "#888";

          row.innerHTML = `
            <div class="pos">${i+1}</div>
            <div class="team-stripe" style="background:${teamColor}"></div>
            <div class="driver-id">
              <div class="driver-name">${d.name}</div>
              <div class="driver-team">${d.team}</div>
            </div>
            <div class="pts-cell" data-role="points">
              <div class="pts-num">${Math.round(d.points)}</div>
              <div class="pts-bar-track"><div class="pts-bar-fill" style="width:${(d.points/maxPoints*100).toFixed(1)}%"></div></div>
            </div>
            ${probFields.map(f => {
              const val = d[f.key];
              const zero = val < 0.005;
              return `
              <div class="prob-cell" data-role="prob" data-cat="${f.cat}">
                <div class="prob-num ${zero ? 'zero' : ''}">${zero ? '—' : pct(val, 2)}</div>
                <div class="prob-bar-track"><div class="prob-bar-fill" style="width:${Math.min(val,100).toFixed(1)}%; opacity:${0.35 + Math.min(val,100)/100*0.65}"></div></div>
              </div>`;
            }).join('')}
          `;

          rowsEl.appendChild(row);

          // attach hover handlers
          row.querySelectorAll('[data-role="prob"]').forEach(cell => {
            cell.addEventListener('mouseenter', (e) => showTooltip(e, d, cell.dataset.cat));
            cell.addEventListener('mousemove', positionTooltip);
            cell.addEventListener('mouseleave', hideTooltip);
          });
          const ptsCell = row.querySelector('[data-role="points"]');
          ptsCell.addEventListener('mouseenter', (e) => showTooltip(e, d, 'points'));
          ptsCell.addEventListener('mousemove', positionTooltip);
          ptsCell.addEventListener('mouseleave', hideTooltip);
        });

    }


  // scrubber.addEventListener('input', (e) => {
  //   // racesLeft = parseInt(e.target.value, 10);
  //   const sliderValue = parseInt(e.target.value,10);
  //   racesLeft = 19 - sliderValue;
  //   renderScrubber();
  //   renderTiles();
  // });

  const boardTitle = document.getElementById("boardTitle");
  const boardNote = document.getElementById("boardNote");

  function renderBoardHeader() {
      // @TODO pull race cities and pair with race num
      const raceCompleted = racesThisSeason - racesLeft;

      boardTitle.innerHTML =
          `Driver Standings &mdash; Projected (After Race ${raceCompleted}, in a ${racesThisSeason} Race Season)`;

      if (raceCompleted > completedRace) {
          boardNote.textContent = "Stay tuned for more updates!";
      } else {
          boardNote.textContent = "Sorted by projected points";
      }
  }

  scrubber.addEventListener("input", e => {

    racesLeft = (maxRacesLeft + 1) - Number(e.target.value);

    drivers = buildDrivers(racesThisSeason - racesLeft);

    renderBoardHeader();

    renderDriverRows();

    renderScrubber();

    renderTiles();

  });

  renderBoardHeader();
  renderDriverRows();
  renderScrubber();
  renderTiles();

})();