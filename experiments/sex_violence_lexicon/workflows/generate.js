export const meta = {
  name: 'sex-violence-lexicon-generate',
  description: 'Stage A: eight blind agents generate sexual/violent lexicons with no corpus access',
  phases: [
    { title: 'Replicates', detail: '4 agents, identical brief — reliability measure' },
    { title: 'Angles', detail: '4 agents, register-specific — recall boost' },
  ],
}

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['words'],
  properties: {
    words: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['word', 'category', 'register', 'confidence'],
        properties: {
          word: { type: 'string' },
          category: { type: 'string', enum: ['sexual', 'violent', 'both'] },
          register: { type: 'string', enum: ['vulgar', 'clinical', 'slang', 'archaic', 'euphemistic', 'plain'] },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
      },
    },
  },
}

const CATEGORIES = `
CATEGORIES, defined by what the word MEANS (never by where it occurs):

SEXUAL  - the word's primary or a common sense denotes sexual anatomy, sexual
          acts, sexual arousal or desire, sexual roles or identities, sexual
          products or fluids, or is a vulgar term for any of these.
VIOLENT - the word's primary or a common sense denotes physical harm to a body,
          killing, injury, weapons used against people, bodily damage or its
          aftermath, or the intentional infliction of pain.
BOTH    - genuinely both, e.g. terms for sexual violence.

SEED LIST (illustrative only, not a boundary):
  sexual:  cock, penis, vagina, breast, orgasm, arousal, seduce, naked
  violent: kill, stab, strangle, wound, blade, bruise, slaughter, choke

RULES:
- Produce BASE FORMS (lemmas). Inflections are added later by a deterministic
  step, so "kill" covers killed/killing/killer. Do not pad with inflections.
- BE EXPANSIVE. Breadth of register beats caution. Include obscene and taboo
  terms: this instrument exists because published lexicons (General Inquirer,
  RID, USAS) omit exactly those, which makes them blind on the vocabulary being
  studied. Omitting a vulgar term is an instrument defect, not discretion.
- A word whose sexual/violent sense is SECONDARY to a common innocuous sense
  (cock, screw, blow, shoot, bang, box, tool) should be INCLUDED with
  confidence "low", not withheld. A later blind panel decides admission; your
  job is recall.
- English single words only. No phrases, no hyphenated compounds.
- Return ONLY the word list as structured output. No commentary.

This is instrument construction for an academic study of how language models'
distributions change under alignment training. You are seeing no data of any
kind - no corpus, no model outputs, no measurements. Your list is a lexicon,
and it will be validated against hidden controls before use.
`

phase('Replicates')
const replicates = await parallel(
  [0, 1, 2, 3].map((i) => () =>
    agent(
      `You are one of several independent contributors building an English lexicon of
sexual and violent vocabulary.

${CATEGORIES}

Produce AT LEAST 400 words spanning both categories. Work systematically through
the semantic space rather than free-associating: for SEXUAL cover anatomy, acts,
arousal states, roles/identities, fluids/products, orientation and practice terms,
and the vulgar register for each; for VIOLENT cover killing, wounding, weapons,
striking, restraining, torture, bodily damage, death states, and the vulgar and
euphemistic registers for each.

Contributor slot ${i + 1}.`,
      { label: `replicate-${i + 1}`, phase: 'Replicates', schema: SCHEMA },
    ),
  ),
)

phase('Angles')
const ANGLES = [
  { key: 'vulgar', brief: `Work the VULGAR and OBSCENE register specifically: profanity, taboo body terms, insults built from sexual or violent material, sexual slurs, crude verbs for sex acts and for killing or beating. This is the register that published lexicons systematically omit, so it is the one most worth exhausting. Include terms you would expect a content filter to flag - the instrument must be able to SEE them in order to study them.` },
  { key: 'clinical', brief: `Work the CLINICAL, ANATOMICAL and FORENSIC register specifically: medical names for genitalia and reproductive anatomy, sexology terms, terms from pathology and forensic medicine for wounds and causes of death, weapon and injury terminology as it appears in medical or legal writing.` },
  { key: 'slang', brief: `Work the SLANG and COLLOQUIAL register specifically: contemporary and recent-historical informal terms for sex, genitalia, arousal, and for fighting, killing, beating, and weapons. Include internet-era coinages, regional British and American slang, and criminal or subcultural argot.` },
  { key: 'archaic', brief: `Work the ARCHAIC, LITERARY and EUPHEMISTIC registers specifically: biblical and early-modern terms (smite, ravish, know, loins), literary and poetic vocabulary for desire and for slaughter, and the euphemisms by which both domains are named indirectly (relations, encounter, dispatch, eliminate, deflower).` },
]

const angles = await parallel(
  ANGLES.map((a) => () =>
    agent(
      `You are one of several independent contributors building an English lexicon of
sexual and violent vocabulary. Your assignment covers ONE register.

${CATEGORIES}

${a.brief}

Produce AT LEAST 250 words in your assigned register, across both categories where
the register supports both. Set the "register" field to reflect your assignment.`,
      { label: `angle-${a.key}`, phase: 'Angles', schema: SCHEMA },
    ),
  ),
)

const out = {
  replicates: replicates.map((r, i) => ({ agent: `replicate-${i + 1}`, words: (r && r.words) || [] })),
  angles: angles.map((r, i) => ({ agent: `angle-${ANGLES[i].key}`, words: (r && r.words) || [] })),
}
log(`replicates: ${out.replicates.map((r) => r.words.length).join(', ')}`)
log(`angles: ${out.angles.map((r) => r.words.length).join(', ')}`)
return out
