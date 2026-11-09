# Standalone cloud renderer

This package contains only the generic media renderer, brand styling, the fictional generated presenter, and dependency/bootstrap instructions. It contains no CRM code, customer records or credentials.

A dedicated public repository lets the daily build use standard GitHub-hosted runners free of charge. The existing private company repository stays private. On 9 November 2026 Dubai the owner explicitly approved publishing this standalone generator: https://github.com/one-step-ai/daily-content-generator .

The upload key is stored only in the new repository's Actions secrets. It can upload today's marketing videos; it is not a Supabase administration key, Meta token or company-mailbox password. Standard Linux runners only, no paid runners, no purchase or upgrade, no artifact storage charges. Output goes directly to the dedicated bounded media bucket. GitHub schedules may be delayed; publication deduplication remains in Supabase.

Published files: marketing/automation/bootstrap.py, daily_video.py, requirements.txt, assets/fictional-presenter.png, UGC rendering helpers, README and the scheduled workflow. No other company-foundation files are included.

Current validation: the business-hack renderer produced a 38.8-second playable H.264/AAC file locally, and it published on both platforms. Linux cloud business-video generation and scoped upload passed in workflow run 42528262210. The first full UGC render and scoped upload also passed in the same run. Its48.32-second720x1280 H.264/AAC export decoded successfully; sampled frames show Arabic captions and the AI label. The first UGC publication succeeded on Facebook and Instagram on9November at the owner's request; normal daily posting remains at20:00Dubai with day/slot deduplication. The generated portrait is fictional and may not be described as a real customer or a real employee.


## Visual quality v2

The owner's revision preserves the English script, voice and speech generation. The presenter now uses the hash-verified512-face checkpoint with natural head movement enabled. Six speech-aligned shots render concurrently on standard public Linux runners, then are assembled with the original uncut speech. The output keeps720x1280/25fps delivery, with a higher-quality bounded encode, large phrase-based Arabic captions, faithful Arabic translations, animated process cards, restrained camera movement and a clear contact CTA. The fictional AI label remains visible.

Generic build inputs and shots use draft GitHub release assets rather than metered Actions artifact/cache storage. No CRM/customer records, Meta tokens or mailbox credentials enter this repository. If the high-detail path fails, a free compatible256-face renderer retains the upgraded graphics and head movement; existing-day preflight and publication deduplication still apply.

Validation: native512 facial rendering passed in run42554678018. A subsequent Linux graphics/export run42558648603 fixed cross-platform Arabic double shaping and passed full decoding. Existing-day duplicate checks passed in42556567420; actual speech preparation and draft-build storage passed in42556571050. A48.32-second six-shot assembly using the existing source footage decoded locally at5790349bytes. That assembly test is separate from the six-second native512 test; a complete new512 daily reel has not yet been published. The enhanced template applies to the next daily UGC, without posting a second UGC today.


## Speech and motion refinement candidate

The manual `speech-motion-preview.yml` workflow tests independent mouth articulation and continuous speech-aware head poses. The original English script and voice stay unchanged. `head_motion.py` adds restrained irregular turns, speech-linked nods, sparse global-timeline blinks and damped vertical translation; short final intervals are merged to avoid abrupt final turns. `ugc_chunks.py` exposes this as an opt-in flag and adds twelve frames of context around section boundaries before trimming each section to its exact global frame range.

`lip_refine.py` uses the official pinned MuseTalk v1.5 model on a separate free CPU runtime. Its feathered mouth-only patch retains the native face outside the lips; models are downloaded from pinned upstream revisions and the large weights are SHA-256 checked. No customer example footage, paid service, GPU rental or new external credential is used. MuseTalk code/model licensing: https://github.com/TMElyralab/MuseTalk . The VAE and Whisper components retain their upstream licenses inside the downloaded model/source directories.

Validation in progress: 406 Python and 156 CRM tests passed; all six context-trim exports matched their exact expected frame counts. The initial three-second dedicated mouth pass rendered and decoded successfully in run42563057445. Independent SyncNet checking on identical three-second speech and comparable tracked face crops measured an offset of minus one frame for both baseline and candidate; confidence increased from7.917 to8.990 and distance decreased from7.834 to6.444. These diagnostics are supporting evidence, not proof of natural motion or creative approval. The first mouth patch softened too much of the beard and was not promoted; a tighter mouth mask is being evaluated. The scheduled renderer remains v2 until the combined visual candidate passes review. SyncNet source: https://github.com/joonson/syncnet_python .

Draft media releases now target the current default branch so a scoped Actions token can save renders even after other workflow changes land. Shell blocks in the preview are checked with Bash syntax validation before dispatch.
