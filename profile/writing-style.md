# Writing style: Ayan Das

Read by every TubeFlow agent and every yt-* skill before writing.

## Voice

A senior student who has been through it, talking to a junior one. Warm, direct and honest about
difficulty. Explains like a good teaching assistant: start from what the viewer already knows, then
add one new idea at a time.

## Teaching it correctly

The goal is that students learn the thing *correctly* and can then learn the next thing alone.

- **Start with the learning goal.** One sentence: "by the end you will be able to ...".
- **Name the prerequisites** in the description and in one spoken line, with a link to learn them.
- **Intuition, then the precise version.** Give the picture first, then the exact definition,
  formula or algorithm. When a simplification is used, say so out loud ("this is simplified; the
  full version is ...").
- **Name the common misconception** and show why it is wrong. Students remember the correction.
- **Worked example before theory gets long.** Real numbers, real data, real code.
- **Let them try.** At least one pause-and-think question per long video, and an exercise at the end
  with its answer in the pinned comment or the linked repo.
- **Point to the next step:** the one resource (paper, book chapter, documentation) to read next.
- **Check before recording:** every fact against a primary source (paper, textbook, official docs),
  every formula re-derived or checked, every number traceable.

## Code and data

- Every piece of code shown on screen has been run, with the output shown being the real output.
  Put the code in the GitHub repo linked in the description, with the library versions.
- Datasets are named and linked, with their licence. No made-up data presented as real.
- Say where results would change: random seeds, data leakage, overfitting, survivorship bias.

## Algorithmic trading and finance

These videos teach the data science and engineering, never what to buy.

- Say "education only, not financial advice" in the opening and in the description.
- No profit promises, no "X% a month", no buy or sell calls, no paid tips or signal groups.
- Every backtest states its period, costs (fees, slippage), and that past results do not predict
  future ones. Show what goes wrong: overfitting, look-ahead bias, survivorship bias.
- Show losses and drawdowns as clearly as gains.
- Be careful with local rules: SEBI (India) restricts unregistered investment advice and
  recommendations. Teaching methods is fine; recommending securities is not.

## Written for AI narration (for now)

Narration is text-to-speech until I record my own voice, so scripts must read cleanly aloud:

- Short sentences of 20 words or fewer. One idea per sentence.
- Spell out what a TTS engine stumbles on: "C N N" or "convolutional neural network", not "CNN" on
  first use; "for example", not "e.g."; "about 30 percent", not "~30%".
- Write numbers the way they should be spoken.
- Put pauses in with line breaks or "...", never with brackets the engine will read out.
- Keep on-screen text (equations, code, paper titles) in a separate `[ON SCREEN: ...]` line so it is
  shown, not read.
- No jokes that rely on tone of voice. TTS flattens them.

## Languages

- **English:** simple international English, no slang that does not travel.
- **Hindi:** conversational Hindi (Hinglish is fine for technical terms students actually say in
  English, such as "neural network" or "algorithm"). Devanagari script for TTS input.
- **Bengali:** conversational Bengali, same rule for technical terms. Bengali script for TTS input.
- Translate the idea, not the words. The hook is rewritten for each language, then scored again.

## Words to avoid

"unlock", "game-changer", "dive in", "let's get into it", "mind-blowing", "secret", "hack your brain".

## Rules for research claims

- Every factual claim about a study names it on screen (author, year), and the description links it.
- Say "one study found" rather than "science says".
- Separate what is known from what is my opinion or my own unpublished work.
- Never invent a number. If a figure is missing, ask for it or write the line without it.

## Calls to action

One per video, at the end: a question for the comments that tells us what to make next.
No "smash that like button".
