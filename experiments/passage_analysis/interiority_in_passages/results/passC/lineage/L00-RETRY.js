export const meta = {
  name: 'passc-L00-retry',
  description: 'BSC-LT/salamandra-7b: one blind coder over 400 passages, 5 fields',
  phases: [{ title: 'Code' }],
}
const FILES = ["/Users/rj416/github/malignment/experiments/interiority_in_passages/results/passC/lineage/batches/L00-b00.json", "/Users/rj416/github/malignment/experiments/interiority_in_passages/results/passC/lineage/batches/L00-b04.json"]
const SCHEMA = { type:'object', properties:{ codings:{ type:'array', items:{ type:'object',
  properties:{ id:{type:'string'}, narrative:{type:'boolean'},
    mode:{type:'string',enum:['NONE','TOLD','SHOWN']},
    drift:{type:'string',enum:['HOLDS','SHIFTS','UNMOORED']},
    degree:{type:'integer',minimum:0,maximum:3}, span:{type:'string'} },
  required:['id','narrative','mode','drift','degree','span'],
  additionalProperties:false } } }, required:['codings'], additionalProperties:false }
phase('Code')
const res = await parallel(FILES.map((f, i) => () => agent(
  'Read /Users/rj416/github/malignment/experiments/interiority_in_passages/results/passC/lineage/rubric.txt -- it is the complete coding scheme. Then read ' + f +
  ', a JSON object keyed by passage id where each entry has "f" (the fragment the model was given)' +
  ' and "c" (what it wrote). Apply the scheme to EVERY passage in that file and return one record' +
  ' per id. Return nothing else.',
  { label: 'L00retry:b' + i, phase: 'Code', schema: SCHEMA, effort: 'high' }
).then(r => (r && r.codings) || [])))
const A = {}
for (const rows of res.filter(Boolean)) for (const c of rows)
  A[c.id] = { narrative: c.narrative, mode: c.mode, drift: c.drift, degree: c.degree, span: c.span }
log('L00 coded ' + Object.keys(A).length)
return { _shard: 900, _pair: 'BSC-LT/salamandra-7b', _files: FILES, A, B: {} }
