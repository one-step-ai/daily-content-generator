# Standalone cloud renderer

This package contains only the generic media renderer, brand styling, the fictional generated presenter, and dependency/bootstrap instructions. It contains no CRM code, customer records or credentials.

A dedicated public repository lets the daily build use standard GitHub-hosted runners free of charge. The existing private company repository stays private. On 9 November 2026 Dubai the owner explicitly approved publishing this standalone generator: https://github.com/one-step-ai/daily-content-generator .

The upload key is stored only in the new repository's Actions secrets. It can upload today's marketing videos; it is not a Supabase administration key, Meta token or company-mailbox password. Standard Linux runners only, no paid runners, no purchase or upgrade, no artifact storage charges. Output goes directly to the dedicated bounded media bucket. GitHub schedules may be delayed; publication deduplication remains in Supabase.

Proposed published files: marketing/automation/bootstrap.py, daily_video.py, requirements.txt, assets/fictional-presenter.png, UGC rendering helpers when validated, README and the scheduled workflow. No other company-foundation files are included.

Current validation: the business-hack renderer produced a 38.8-second playable H.264/AAC file locally, and it published on both platforms. Linux cloud execution and UGC generation have not yet been validated. The generated portrait is fictional and may not be described as a real customer or a real employee.
