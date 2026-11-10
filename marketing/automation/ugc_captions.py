"""Faithful Arabic captions for the unchanged, reviewed English presenter script."""
TITLES={
 'Give every lead a next action':'حدد خطوة تالية لكل عميل محتمل.',
 'Make your contact page work harder':'اجعل صفحة التواصل أكثر فاعلية.',
 'Stop relying on memory for follow-ups':'لا تعتمد على الذاكرة في متابعة العملاء.',
 'Clean your pipeline before automating':'نظّم مراحل المبيعات قبل الأتمتة.',
 'Build a clearer team handoff':'اجعل تسليم العمل بين أعضاء الفريق أكثر وضوحًا.',
 'Automate one repeated task first':'ابدأ بأتمتة مهمة متكررة واحدة.',
 'Turn a reply into a useful next step':'حوّل كل رد إلى خطوة تالية مفيدة.',
 'Connect your form to follow-up':'اربط نموذج التواصل بمتابعة العملاء.',
 'Make your sales stages useful':'اجعل مراحل المبيعات مفيدة لفريقك.',
 'Map the process before choosing tools':'ارسم خطوات العمل قبل اختيار الأدوات.',
 'Give your website one clear next step':'اجعل لموقعك خطوة تالية واضحة.',
 'Keep customer context together':'احتفظ بتفاصيل العميل في مكان واحد.',
 'Build useful reminders':'أنشئ تذكيرات تساعد فريقك على العمل.',
 'Create a handoff checklist':'أنشئ قائمة تحقق لتسليم العمل.',
 'Make enquiry tracking a daily habit':'اجعل متابعة الاستفسارات عادة يومية.',
}


def caption(data,cue):
    if data.get('verbatim_arabic'):return cue['ar']
    english=cue['en']
    if english.startswith('Here is a practical idea for organising your business enquiries.'):
        return 'إليك فكرة عملية لتنظيم استفسارات العملاء في شركتك. '+TITLES.get(data.get('title'),cue['ar'])
    if english.endswith('Keep this step clear and useful for your team.'):
        return cue['ar']+' اجعل هذه الخطوة واضحة ومفيدة لفريقك.'
    if english.startswith('Start with one workflow and check it with a real enquiry'):
        return 'ابدأ بعملية واحدة واختبرها باستفسار حقيقي قبل توسيعها. يجب أن تتوافق العملية مع الطريقة التي يعمل بها فريقك فعليًا.'
    if english.startswith('At One Step, we build websites, CRM systems and enquiry automations.'):
        return 'في ون ستيب، نطوّر المواقع وأنظمة إدارة علاقات العملاء وأتمتة الاستفسارات. راسل ون ستيب لمناقشة نقطة انطلاق عملية تناسب شركتك.'
    return cue['ar']
