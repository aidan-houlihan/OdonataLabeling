const ID=['scientificName','scientificNameAuthorship','identifiedBy','dateIdentified'];
const states=new Set('AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC Alabama Alaska Arizona Arkansas California Colorado Connecticut Delaware Florida Georgia Hawaii Idaho Illinois Indiana Iowa Kansas Kentucky Louisiana Maine Maryland Massachusetts Michigan Minnesota Mississippi Missouri Montana Nebraska Nevada New Hampshire New Jersey New Mexico New York North Carolina North Dakota Ohio Oklahoma Oregon Pennsylvania Rhode Island South Carolina South Dakota Tennessee Texas Utah Vermont Virginia Washington West Virginia Wisconsin Wyoming District of Columbia'.split('|'));
const stateNames=['Alabama','Alaska','Arizona','Arkansas','California','Colorado','Connecticut','Delaware','Florida','Georgia','Hawaii','Idaho','Illinois','Indiana','Iowa','Kansas','Kentucky','Louisiana','Maine','Maryland','Massachusetts','Michigan','Minnesota','Mississippi','Missouri','Montana','Nebraska','Nevada','New Hampshire','New Jersey','New Mexico','New York','North Carolina','North Dakota','Ohio','Oklahoma','Oregon','Pennsylvania','Rhode Island','South Carolina','South Dakota','Tennessee','Texas','Utah','Vermont','Virginia','Washington','West Virginia','Wisconsin','Wyoming','District of Columbia'];
const stateAbbr='AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split(' ');
const isUSState=v=>stateNames.some(x=>x.toLowerCase()===(v||'').trim().toLowerCase())||stateAbbr.includes((v||'').trim().toUpperCase());
const groups={
'Collector Info':['catalogNumber','recordedBy','recordNumber','eventDate','endDayOfYear','verbatimEventDate','associatedCollectors'],
'Latest Identification':['scientificName','scientificNameAuthorship','identificationQualifier','family','identifiedBy','dateIdentified'],
'Locality':['continent','country','stateProvince','county','municipality','locationID','locality','decimalLatitude','decimalLongitude','coordinateUncertaintyInMeters','geodeticDatum','verbatimCoordinates','minimumElevationInMeters','maximumElevationInMeters','verbatimElevation','georeferencedBy','georeferenceSources','georeferenceRemarks','georeferenceProtocol','georeferenceVerificationStatus'],
'Misc':['habitat','substrate','associatedTaxa','occurrenceRemarks','lifeStage','sex','individualCount','samplingProtocol','preparations','behavior','vitality','establishmentMeans'],
'Curation':['typeStatus','disposition','occurrenceID','fieldNumber','language','institutionCode','collectionCode','ownerInstitutionCode','storageLocation','basisOfRecord','processingStatus']};
let records=[{}], current=0, fields=[];
const defaults={scientificName:[1,'','',' ','scientific',0,0,'','Helvetica','',1],scientificNameAuthorship:[1,'','',' ','normal',1,0,'','Helvetica','',1],identifiedBy:[1,'det. ','',' ','normal',1,0,'','Helvetica','',1],dateIdentified:[0,'','',' ','date',1,0,'','Helvetica','',1],sex:[1,'','',' ','normal',1,0,'','Helvetica','',1],locality:[1,'','',', ','normal',1,0,'','Helvetica','',1],municipality:[1,'','',', ','normal',0,0,'','Helvetica','',1],county:[1,'','',', ','normal',0,0,'','Helvetica','',1],stateProvince:[1,'','',', ','bold',0,0,'','Helvetica','',1],country:[1,'','',' ','bold',1,0,'','Helvetica','',1],decimalLatitude:[1,'','',', ','normal',0,0,'','Helvetica','',1],decimalLongitude:[1,'','',', ','normal',1,0,'','Helvetica','',1],verbatimElevation:[1,'elev. ','',' ','normal',1,0,'','Helvetica','',1],eventDate:[1,'','','    ','date',0,0,'','Helvetica','',1],habitat:[1,'','',' ','normal',1,0,'','Helvetica','',1],recordedBy:[1,'coll. ','','    ','normal',0,0,'','Helvetica','',1],fieldNumber:[1,'field no. ','',' ','normal',1,0,'','Helvetica','',1]};
function cfg(name){let d=defaults[name]||[0,'','',' ','normal',1,0,'','Helvetica','',1];return {name,include:!!d[0],prefix:d[1],suffix:d[2],separator:d[3],format:d[4],newline:!!d[5],blank:+d[6],wrap:d[7],font:d[8],size:d[9],spacing:+d[10]}}
function ensureFields(names){if(!Array.isArray(fields))fields=[];let set=new Set(fields.map(x=>x.name));ID.forEach(n=>{if(!set.has(n)){fields.unshift(cfg(n));set.add(n)}});names.forEach(n=>{if(!set.has(n)){fields.push(cfg(n));set.add(n)}});fields.sort((a,b)=>{let ai=ID.indexOf(a.name),bi=ID.indexOf(b.name);if(ai>=0||bi>=0)return (ai<0?99:ai)-(bi<0?99:bi);return 0})}
ensureFields(Object.values(groups).flat());
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function parseCSV(t){let rows=[],row=[],v='',q=false;for(let i=0;i<t.length;i++){let c=t[i];if(q){if(c==='"'&&t[i+1]==='"'){v+='"';i++}else if(c==='"')q=false;else v+=c}else if(c==='"')q=true;else if(c===','){row.push(v);v=''}else if(c==='\n'){row.push(v.replace(/\r$/,''));rows.push(row);row=[];v=''}else v+=c}if(v||row.length){row.push(v);rows.push(row)}let h=rows.shift()||[];return rows.filter(r=>r.some(Boolean)).map(r=>Object.fromEntries(h.map((x,i)=>[x,r[i]??''])))}
function csvEscape(v){v=String(v??'');return /[",\n]/.test(v)?'"'+v.replaceAll('"','""')+'"':v}
function download(name,text,type='application/json'){let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}
function allRecordFields(){let fs=Array.isArray(fields)?fields:[];return [...new Set([...Object.values(groups).flat(),...fs.map(x=>x.name),...records.flatMap(r=>Object.keys(r))])]}
function renderForm(){let form=document.querySelector('#occForm');form.innerHTML='';for(let [title,names] of Object.entries(groups)){let g=document.createElement('fieldset');g.className='group';g.innerHTML=`<h2>${title}</h2><div class="grid"></div>`;let grid=g.querySelector('.grid');names.forEach(n=>{let d=document.createElement('div');d.className='field '+(['locality','occurrenceRemarks','associatedTaxa','georeferenceRemarks'].includes(n)?'full':'');let val=records[current]?.[n]||'';let multi=['locality','occurrenceRemarks','associatedTaxa','georeferenceRemarks','preparations'].includes(n);d.innerHTML=`<label>${label(n)}</label>${multi?`<textarea data-field="${n}">${esc(val)}</textarea>`:`<input data-field="${n}" value="${esc(val)}">`}`;grid.append(d)});form.append(g)}form.querySelectorAll('[data-field]').forEach(x=>x.oninput=()=>{records[current][x.dataset.field]=x.value;updatePreview()});updateRecordNav()}
function label(n){return n.replace(/([A-Z])/g,' $1').replace(/^./,c=>c.toUpperCase()).replace('Recorded By','Collector / Observer').replace('Scientific Name Authorship','Author')}
function updateRecordNav(){let opts=records.map((r,i)=>`<option value="${i}">${i+1}: ${esc(r.catalogNumber||r.scientificName||'new record')}</option>`).join('');for(let id of ['recordSelect','previewRecord'])document.getElementById(id).innerHTML=opts;recordSelect.value=previewRecord.value=current;recordCount.textContent=`${current+1} of ${records.length}`}
function renderFields(){let tb=document.querySelector('#fieldTable tbody');tb.innerHTML='';fields.forEach((f,i)=>{let tr=document.createElement('tr');tr.draggable=!ID.includes(f.name);if(ID.includes(f.name))tr.className='fixed';tr.dataset.i=i;tr.innerHTML=`<td class="drag">${ID.includes(f.name)?'🔒':'☰'}</td><td><input class="sel" type="checkbox"><input data-k="include" type="checkbox" ${f.include?'checked':''}></td><td class="fname">${esc(f.name)}</td><td><input data-k="prefix" value="${esc(f.prefix)}"></td><td><input data-k="suffix" value="${esc(f.suffix)}"></td><td><input data-k="separator" value="${esc(f.separator)}"></td><td><input data-k="newline" type="checkbox" ${f.newline?'checked':''}></td><td><input data-k="blank" type="number" min="0" value="${f.blank}"></td><td><input data-k="wrap" type="number" step=".1" min=".5" max="4.7" value="${f.wrap}"></td><td><select data-k="font">${['Helvetica','Times','Courier'].map(x=>`<option ${f.font===x?'selected':''}>${x}</option>`)}</select></td><td><input data-k="size" type="number" step=".5" min="4" max="30" value="${f.size}"></td><td><input data-k="spacing" type="number" step=".1" min=".1" max="5" value="${f.spacing}"></td><td><select data-k="format">${['normal','bold','italic','scientific','date'].map(x=>`<option ${f.format===x?'selected':''}>${x}</option>`)}</select></td>`;tb.append(tr);tr.querySelectorAll('[data-k]').forEach(el=>el.oninput=()=>{let k=el.dataset.k;f[k]=el.type==='checkbox'?el.checked:(['blank','spacing'].includes(k)?+el.value:el.value);if(f.name==='habitat')f.prefix='';if(['stateProvince','country'].includes(f.name))f.format='bold';updatePreview()});tr.ondragstart=e=>e.dataTransfer.setData('text/plain',i);tr.ondragover=e=>e.preventDefault();tr.ondrop=e=>{e.preventDefault();let from=+e.dataTransfer.getData('text/plain'),to=i;if(ID.includes(fields[from].name)||ID.includes(fields[to].name))return;let [x]=fields.splice(from,1);fields.splice(to,0,x);renderFields();updatePreview()}})}
function fmtDate(v){if(!/^\d{4}-\d\d-\d\d/.test(v||''))return v||'';let d=new Date(v+'T00:00:00');return `${d.getDate()} ${d.toLocaleString('en',{month:'short'})} ${d.getFullYear()}`}
function sex(v){v=(v||'').trim().toLowerCase();return v.includes('female')||v==='f'||v.includes('♀')?'Female':v.includes('male')||v==='m'||v.includes('♂')?'Male':''}
function value(name,r,f){if(name==='country'&&!r.country&&isUSState(r.stateProvince))return 'USA';let v=r[name]||'';return f.format==='date'?fmtDate(v):v}
function orderedItems(r){let arr=[];for(let f of fields){if(!f.include||f.name==='sex')continue;let v=value(f.name,r,f);if(!v)continue;arr.push({...f,value:v,prefix:f.name==='habitat'?'':f.prefix,format:['stateProvince','country'].includes(f.name)?'bold':f.format})}let ids=arr.filter(x=>ID.includes(x.name)).sort((a,b)=>ID.indexOf(a.name)-ID.indexOf(b.name));return [...ids,...arr.filter(x=>!ID.includes(x.name))]}
function logicalLines(r){let a=orderedItems(r),out=[],cur=[];for(let i=0;i<a.length;i++){let x=a[i],next=a[i+1];cur.push(x);let endId=ID.includes(x.name)&&(!next||!ID.includes(next.name));if(endId){out.push({items:cur,blank:1});cur=[]}else if(x.newline){out.push({items:cur,blank:+x.blank||0});cur=[]}}if(cur.length)out.push({items:cur,blank:0});return out}
function updatePreview(){let r=records[current]||{},box=labelPreview;box.innerHTML='';let m=labelMargins();box.style.padding=`${m.top/3*100}% ${m.right/5*100}% ${m.bottom/3*100}% ${m.left/5*100}%`;let lines=logicalLines(r);lines.forEach(line=>{let d=document.createElement('div');d.className='line';line.items.forEach((x,i)=>{let span=document.createElement('span');let fam=x.font==='Times'?'Times New Roman':x.font==='Courier'?'Courier New':'Arial';span.style.fontFamily=fam;span.style.fontWeight=['bold','scientific'].includes(x.format)?'bold':'normal';span.style.fontStyle=['italic','scientific'].includes(x.format)?'italic':'normal';if(x.size)span.style.fontSize=(+x.size/10)+'em';span.style.wordSpacing=((+x.spacing||1)-1)*.28+'em';span.textContent=(x.prefix||'')+x.value+(x.suffix||'')+(i<line.items.length-1?(x.separator||''):'');d.append(span)});box.append(d);for(let j=0;j<line.blank;j++){let b=document.createElement('div');b.className='blank';box.append(b)}});let s=sex(r.sex);if(s){let q=document.createElement('div');q.className='sex';q.style.right=(m.right/5*100)+'%';q.style.top=(m.top/3*100)+'%';q.textContent=s;box.append(q)}updateRecordNav()}
function pdfFont(doc,f){let fam=f.font==='Times'?'times':f.font==='Courier'?'courier':'helvetica',style=f.format==='scientific'?'bolditalic':f.format==='bold'?'bold':f.format==='italic'?'italic':'normal';doc.setFont(fam,style)}

function labelMargins(){return {left:+marginLeft.value||0,right:+marginRight.value||0,top:+marginTop.value||0,bottom:+marginBottom.value||0}}
function pdfTokenWidth(doc,text,f,size){
  // Calculate width explicitly in INCHES. jsPDF getTextWidth() has behaved
  // inconsistently with unit:'in' across builds, which caused same-line fields
  // to advance by almost zero and print on top of each other.
  pdfFont(doc,f); doc.setFontSize(size);
  const unitWidth=doc.getStringUnitWidth(text);
  let width=unitWidth*size/72;
  if(/^\s+$/.test(text)) width*= (+f.spacing||1);
  return width;
}
function pdfTokens(line){
  let out=[];
  line.items.forEach((f,i)=>{
    let txt=(f.prefix||'')+f.value+(f.suffix||'')+(i<line.items.length-1?(f.separator||''):'');
    for(let part of txt.split(/(\s+)/)) if(part) out.push({text:part,f});
  });
  return out;
}

function drawPdfLabel(doc,r,x,y){
  const m=labelMargins(), left=x+m.left, maxW=Math.max(.5,5-m.left-m.right), base=10, leading=1.16;
  let cy=y+m.top+.12, renderedLines=0;
  for(let line of logicalLines(r)){
    let wraps=line.items.map(f=>+f.wrap).filter(v=>v>0);
    let lineW=Math.min(maxW,wraps.length?Math.min(...wraps):maxW);
    // Keep the first two rendered lines clear of the upper-right sex symbol.
    if(renderedLines<2 && sex(r.sex)) lineW=Math.min(lineW,maxW-.70);
    let cx=left, linePt=base, used=false;
    for(let t of pdfTokens(line)){
      let f=t.f,size=+f.size||base;
      pdfFont(doc,f);doc.setFontSize(size);
      let w=pdfTokenWidth(doc,t.text,f,size);
      if(!/^\s+$/.test(t.text) && used && cx-left+w>lineW){
        cy+=linePt/72*leading;renderedLines++;cx=left;linePt=size;used=false;
        if(renderedLines<2 && sex(r.sex)) lineW=Math.min(lineW,maxW-.70);
      }
      if(/^\s+$/.test(t.text)){
        if(used) cx+=w;
      }else{
        doc.text(t.text,cx,cy);cx+=w;linePt=Math.max(linePt,size);used=true;
      }
    }
    cy+=linePt/72*leading;renderedLines++;
    if(+line.blank) cy+=(+line.blank)*linePt/72*leading;
  }
  let s=sex(r.sex);
  if(s){doc.setFont('helvetica','normal');doc.setFontSize(11);doc.text(s,x+5-m.right,y+m.top+.12,{align:'right'});}
  if(borders.checked){doc.setLineWidth(.005);doc.rect(x,y,5,3)}
}
function makePDF(){if(!window.jspdf)return msg('PDF library did not load. GitHub Pages needs internet access for the jsPDF CDN.');let {jsPDF}=window.jspdf;/* Landscape Letter fits four 5 x 3 labels directly as a centered contiguous 10 x 6 block. Avoiding PDF transformation matrices fixes blank PDFs in some jsPDF/browser combinations. */let doc=new jsPDF({unit:'in',format:'letter',orientation:'landscape'});let pos=[[.5,1.25],[5.5,1.25],[.5,4.25],[5.5,4.25]];records.forEach((r,i)=>{if(i&&i%4===0)doc.addPage();let [px,py]=pos[i%4];drawPdfLabel(doc,r,px,py)});doc.save('odonata_labels.pdf')}
function msg(t){message.querySelector('p').textContent=t;message.showModal()}
function setTab(id){document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x.id===id));document.querySelectorAll('nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));if(id==='layout')renderFields();if(id==='preview')updatePreview()}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>setTab(b.dataset.tab));
csvFile.onchange=async()=>{let rs=parseCSV(await csvFile.files[0].text());if(!rs.length)return msg('No records found.');records=rs;current=0;ensureFields(Object.keys(rs[0]));renderForm();renderFields();updatePreview()};
newRecord.onclick=()=>{records.push({});current=records.length-1;renderForm();updatePreview()};duplicateRecord.onclick=()=>{records.push({...records[current]});current=records.length-1;renderForm();updatePreview()};deleteRecord.onclick=()=>{if(records.length===1)records=[{}];else records.splice(current,1);current=Math.min(current,records.length-1);renderForm();updatePreview()};
recordSelect.onchange=e=>{current=+e.target.value;renderForm();updatePreview()};previewRecord.onchange=e=>{current=+e.target.value;renderForm();updatePreview()};
includeSelected.onclick=()=>{document.querySelectorAll('#fieldTable tbody tr').forEach((tr,i)=>{if(tr.querySelector('.sel').checked)fields[i].include=true});renderFields();updatePreview()};excludeSelected.onclick=()=>{document.querySelectorAll('#fieldTable tbody tr').forEach((tr,i)=>{if(tr.querySelector('.sel').checked)fields[i].include=false});renderFields();updatePreview()};selectIncluded.onclick=()=>document.querySelectorAll('#fieldTable tbody tr').forEach((tr,i)=>tr.querySelector('.sel').checked=fields[i].include);
function normalizeTemplate(t){
  if(!t || typeof t!=='object') throw new Error('Template root must be a JSON object.');
  // Native web templates store fields as an array. Desktop Python templates
  // store fields as an object keyed by Darwin Core field name plus fieldOrder.
  if(Array.isArray(t.fields)) return t.fields.map(x=>({...cfg(x.name),...x}));
  if(t.fields && typeof t.fields==='object'){
    let order=t.fieldOrder||t.order||Object.keys(t.fields);
    let seen=new Set(), out=[];
    for(let name of order){
      if(!t.fields[name]||seen.has(name)) continue;
      let x=t.fields[name], base=cfg(name);
      out.push({...base,...x,name,
        blank:x.blank_lines??x.blank??base.blank,
        wrap:x.wrap_width??x.wrap??base.wrap,
        font:x.font_family??x.font??base.font,
        size:x.font_size??x.size??base.size,
        spacing:x.word_spacing??x.spacing??base.spacing
      });
      seen.add(name);
    }
    for(let [name,x] of Object.entries(t.fields)){
      if(seen.has(name)) continue;
      let base=cfg(name);
      out.push({...base,...x,name,blank:x.blank_lines??x.blank??base.blank,wrap:x.wrap_width??x.wrap??base.wrap,font:x.font_family??x.font??base.font,size:x.font_size??x.size??base.size,spacing:x.word_spacing??x.spacing??base.spacing});
    }
    return out;
  }
  throw new Error('Template has no recognizable fields section.');
}
saveTemplate.onclick=()=>download('odonata_label_template.json',JSON.stringify({templateType:'Odonata Label Studio Template',version:3,fieldOrder:fields.map(x=>x.name),fields,borders:borders.checked,margins:labelMargins()},null,2));
loadTemplate.onclick=()=>templateFile.click();
templateFile.onchange=async()=>{try{let t=JSON.parse(await templateFile.files[0].text());fields=normalizeTemplate(t);borders.checked=!!(t.borders??t.showCuttingBorders);let m=t.margins||{};marginLeft.value=m.left??.16;marginRight.value=m.right??.16;marginTop.value=m.top??.15;marginBottom.value=m.bottom??.13;ensureFields(allRecordFields());renderFields();updatePreview();}catch(e){msg('Could not load template: '+e.message)}finally{templateFile.value=''}};
exportCsv.onclick=()=>{let h=allRecordFields();let text=h.map(csvEscape).join(',')+'\n'+records.map(r=>h.map(k=>csvEscape(r[k]||'')).join(',')).join('\n');download('odonata_occurrences.csv',text,'text/csv')};makePdf.onclick=makePDF;borders.onchange=updatePreview;[marginLeft,marginRight,marginTop,marginBottom].forEach(x=>x.oninput=updatePreview);
renderForm();renderFields();updatePreview();
