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
