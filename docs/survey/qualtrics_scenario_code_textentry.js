Qualtrics.SurveyEngine.addOnload(function () {
  var SCENARIO_INDEX = 0;   // <-- CHANGE PER QUESTION: 0, 1, 2, or 3
  var MAX_OPEN = 4;

  var SCENARIOS = [
    { id:"Q1", domain:"Public health", frame:"gain", ambiguity:"precise",
      intro:"A community faces an outbreak expected to affect 600 people. You must choose one response program.",
      safe:"200 people are saved for certain.",
      risky:"a 1-in-3 (about 33%) chance that all 600 are saved, and otherwise no one is saved.",
      cards:[
        {k:"Cost",safe:"Moderate, fixed public-health budget.",risky:"Comparable total cost, spent up front.",threat:false},
        {k:"Benefits",safe:"Guarantees 200 people saved.",risky:"Chance to save all 600 people.",threat:false},
        {k:"Timing",safe:"Takes effect immediately.",risky:"Effect is delayed about two weeks.",threat:false},
        {k:"Reliability",safe:"Outcome is certain.",risky:"Depends on an uncertain transmission response.",threat:false},
        {k:"Worst case",safe:"400 people are not saved.",risky:"With about 67% probability, no one is saved.",threat:true},
        {k:"Side effects",safe:"Mild, well-documented side effects in the treated group.",risky:"Unknown side-effect profile if scaled to all 600.",threat:true},
        {k:"Who is affected",safe:"A known subgroup of 200 people.",risky:"The entire population of 600 is exposed to the gamble.",threat:true}
      ]},
    { id:"Q2", domain:"Financial reserves", frame:"gain", ambiguity:"ambiguous",
      intro:"An organization can protect part of a $600,000 reserve fund that is at risk.",
      safe:"$200,000 is preserved for certain.",
      risky:"an unknown chance—plausibly between 10% and 50%—that the full $600,000 is preserved, and otherwise none is preserved.",
      cards:[
        {k:"Cost",safe:"Low administrative cost.",risky:"Moderate transaction cost.",threat:false},
        {k:"Benefits",safe:"Secures $200,000.",risky:"Chance to secure the full $600,000.",threat:false},
        {k:"Timing",safe:"Settled this quarter.",risky:"Resolves next fiscal year.",threat:false},
        {k:"Reliability",safe:"Guaranteed outcome.",risky:"Probability is not precisely known (est. 10–50%).",threat:false},
        {k:"Worst case",safe:"$400,000 is lost.",risky:"Likely (est. 50–90%) that the full $600,000 is lost.",threat:true},
        {k:"Side effects",safe:"Minor short-term liquidity constraint.",risky:"Possible covenant breach if the gamble fails.",threat:true},
        {k:"Who is affected",safe:"The reserve fund only.",risky:"The reserve plus dependent operating accounts.",threat:true}
      ]},
    { id:"Q3", domain:"Infrastructure", frame:"loss", ambiguity:"precise",
      intro:"A storm threatens 600 units of municipal equipment.",
      safe:"400 units are lost for certain.",
      risky:"a 1-in-3 (about 33%) chance that nothing is lost, and otherwise all 600 units are lost.",
      cards:[
        {k:"Cost",safe:"Fixed repair cost.",risky:"Comparable cost, contingent on the outcome.",threat:false},
        {k:"Benefits",safe:"Retains 200 units.",risky:"Chance to retain all 600 units.",threat:false},
        {k:"Timing",safe:"Completed before the storm.",risky:"Outcome known only after the storm.",threat:false},
        {k:"Reliability",safe:"Outcome is certain.",risky:"A 1-in-3 chance of success.",threat:false},
        {k:"Worst case",safe:"400 units are lost.",risky:"A 2-in-3 chance that all 600 units are lost.",threat:true},
        {k:"Side effects",safe:"Service disruption in the repaired zones.",risky:"Cascading outages if all units are lost.",threat:true},
        {k:"Who is affected",safe:"Identified districts.",risky:"The entire municipality is at risk.",threat:true}
      ]},
    { id:"Q4", domain:"Wildfire response", frame:"loss", ambiguity:"ambiguous",
      intro:"A wildfire threatens 600 hectares of protected forest.",
      safe:"400 hectares are lost for certain.",
      risky:"an unknown chance—plausibly between 10% and 50%—that no hectares are lost, and otherwise all 600 are lost.",
      cards:[
        {k:"Cost",safe:"Fixed suppression cost.",risky:"Variable, weather-dependent cost.",threat:false},
        {k:"Benefits",safe:"Saves 200 hectares.",risky:"Chance to save all 600 hectares.",threat:false},
        {k:"Timing",safe:"Crews deploy now.",risky:"Depends on a wind shift; timing uncertain.",threat:false},
        {k:"Reliability",safe:"Outcome is certain.",risky:"Probability is not precisely known (est. 10–50%).",threat:false},
        {k:"Worst case",safe:"400 hectares are lost.",risky:"Likely (est. 50–90%) that all 600 hectares are lost.",threat:true},
        {k:"Side effects",safe:"Smoke impact in one valley.",risky:"Watershed and habitat loss if all burns.",threat:true},
        {k:"Who is affected",safe:"One forest tract.",risky:"Adjacent tracts and the downstream water supply.",threat:true}
      ]}
  ];

  var qthis = this;
  var s = SCENARIOS[SCENARIO_INDEX];
  function shuffle(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t;}return a;}
  function esc(x){return String(x).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

  var safeIsA = Math.random() < 0.5;
  var cardOrder = shuffle(s.cards);
  var opened = [], choice = null, t0 = Date.now();

  var cont = this.getQuestionContainer();

  // --- hide the Text Entry input box (we save into it, but respondents never see it) ---
  var inp = cont.querySelector("textarea, input[type=text]");
  if (inp) { inp.style.cssText = "position:absolute;left:-9999px;width:1px;height:1px;opacity:0;"; inp.setAttribute("tabindex","-1"); }

  if (!document.getElementById("rfStyle")) {
    var st = document.createElement("style"); st.id = "rfStyle";
    st.innerHTML =
      ".rf{font-size:16px;line-height:1.5;padding:0 14px;max-width:760px;margin:0 auto}"+
      ".rf *{box-sizing:border-box}"+
      ".rf .intro{font-size:17px}"+
      ".rf .opt{margin:6px 0}.rf .opt b{color:#0f6d6b}"+
      ".rf .cnt{font-size:13px;color:#666;margin:12px 0 4px}"+
      ".rf .grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0}"+
      ".rf .card{text-align:center !important;width:100%;min-width:0;border:1px solid #ccc;border-radius:10px;padding:12px;background:#fff;cursor:pointer;min-height:48px}"+
      ".rf .card:last-child{grid-column:1 / -1}"+
      ".rf .card .k{font-weight:700;display:block}"+
      ".rf .card .v{display:none;margin-top:10px}"+
      ".rf .card .oa,.rf .card .ob{display:block;text-align:left;color:#555;font-size:14px;overflow-wrap:break-word}"+
      ".rf .card .ob{margin-top:10px}"+
      ".rf .card.open{background:#e9f2f1;border-color:#0f6d6b}.rf .card.open .v{display:block}"+
      ".rf .card[disabled]{opacity:.5;cursor:not-allowed}"+
      ".rf .choices{display:flex;gap:12px;margin-top:8px}"+
      ".rf .ch{flex:1 1 0;min-width:0;border:2px solid #ccc;border-radius:10px;padding:14px;background:#fff;cursor:pointer;font-weight:600;text-align:center}"+
      ".rf .ch.sel{border-color:#0f6d6b;background:#e9f2f1}";
    document.head.appendChild(st);
  }

  var aOpt = safeIsA ? s.safe : s.risky;
  var bOpt = safeIsA ? s.risky : s.safe;
  var cardsHtml = cardOrder.map(function(c){
    var aT = safeIsA ? c.safe : c.risky, bT = safeIsA ? c.risky : c.safe;
    return '<button type="button" class="card" data-k="'+esc(c.k)+'">'+
             '<span class="k">'+esc(c.k)+'</span>'+
             '<span class="v"><span class="oa"><b>Option A:</b> '+esc(aT)+'</span><span class="ob"><b>Option B:</b> '+esc(bT)+'</span></span>'+
           '</button>';
  }).join("");

  var box = document.createElement("div");
  box.className = "rf";
  box.innerHTML =
    '<p class="intro"><b>Scenario '+(SCENARIO_INDEX+1)+' of 4 — '+esc(s.domain)+'.</b> '+esc(s.intro)+'</p>'+
    '<p class="opt"><b>Option A:</b> '+aOpt+'</p>'+
    '<p class="opt"><b>Option B:</b> '+bOpt+'</p>'+
    '<p class="cnt">Open up to '+MAX_OPEN+' information cards before you choose (fewer is fine). <span class="rem"></span></p>'+
    '<div class="grid">'+cardsHtml+'</div>'+
    '<p class="cnt">Your choice:</p>'+
    '<div class="choices"><button type="button" class="ch" data-s="A">Choose Option A</button>'+
    '<button type="button" class="ch" data-s="B">Choose Option B</button></div>';
  cont.appendChild(box);

  var qText = cont.querySelector(".QuestionText");
  if (qText) { qText.style.textAlign = "center"; }

  qthis.disableNextButton();

  function saveRec(){
    var nThreat = 0;
    opened.forEach(function(k){ var cc=s.cards.filter(function(x){return x.k===k;})[0]; if(cc&&cc.threat)nThreat++; });
    var rec = { id:s.id, frame:s.frame, ambiguity:s.ambiguity, safeOption: safeIsA?"A":"B",
      cardsOpened:opened.slice(), nOpened:opened.length, nThreat:nThreat,
      threatShare: opened.length ? Math.round(nThreat/opened.length*1000)/1000 : null,
      choice:choice, ms: Date.now()-t0 };
    var val = JSON.stringify(rec);
    // save into this question's hidden Text Entry box.
    // The new survey engine uses a React-controlled input, so plain inp.value is ignored;
    // we must call the native value setter, then dispatch input/change so React records it.
    if (inp) {
      try {
        var proto = (inp.tagName === "TEXTAREA") ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype;
        var nativeSet = Object.getOwnPropertyDescriptor(proto, "value").set;
        nativeSet.call(inp, val);
      } catch(e) { inp.value = val; }
      inp.dispatchEvent(new Event("input", {bubbles:true}));
      inp.dispatchEvent(new Event("change", {bubbles:true}));
    }
    // harmless backup if ever run on the classic engine
    try { Qualtrics.SurveyEngine.setEmbeddedData("S"+(SCENARIO_INDEX+1)+"_data", val); } catch(e){}
  }

  var cardEls = box.querySelectorAll(".card");
  function updateRem(){
    var left = MAX_OPEN - opened.length;
    box.querySelector(".rem").textContent = left>0 ? "("+left+" left)" : "(limit reached)";
    if(left<=0){ cardEls.forEach(function(b){ if(!b.classList.contains("open")) b.setAttribute("disabled","disabled"); }); }
  }
  updateRem();
  cardEls.forEach(function(b){
    b.onclick = function(){
      if(b.classList.contains("open") || opened.length>=MAX_OPEN) return;
      b.classList.add("open"); opened.push(b.getAttribute("data-k")); updateRem();
    };
  });

  var chEls = box.querySelectorAll(".ch");
  chEls.forEach(function(b){
    b.onclick = function(){
      choice = (b.getAttribute("data-s")==="A") ? (safeIsA?"safe":"risky") : (safeIsA?"risky":"safe");
      chEls.forEach(function(x){ x.classList.remove("sel"); }); b.classList.add("sel");
      saveRec(); qthis.enableNextButton();
    };
  });
});
