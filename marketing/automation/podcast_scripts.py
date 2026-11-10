"""Reviewed factual short podcast scripts; no fabricated customer story or result."""
from datetime import date

TOPICS=[
 ('Fix the follow-up first',[
  ('More enquiries will not fix a broken follow-up.','زيادة الاستفسارات لا تعالج مشكلة ضعف المتابعة.'),
  ('Put every enquiry in one place.','اجمع كل استفسارات العملاء في مكان واحد.'),
  ('Give it an owner, a next step, and a reminder.','حدّد مسؤولاً عن كل استفسار، وخطوة تالية، وتذكيراً بالمتابعة.'),
  ('Your team can see what needs attention.','بهذه الطريقة، يعرف فريقك ما يحتاج إلى المتابعة.')]),
 ('Make the next step clear',[
  ('A new lead needs more than a name.','العميل المحتمل الجديد يحتاج إلى أكثر من مجرد تسجيل اسمه.'),
  ('Record what the person asked for.','سجّل ما طلبه الشخص بالتحديد.'),
  ('Choose who replies and when to follow up.','حدّد من سيردّ عليه ومتى ستتم المتابعة.'),
  ('Keep the next action visible to your team.','اجعل الخطوة التالية واضحة أمام فريقك.')]),
 ('Start with one workflow',[
  ('Where should your business start with automation?','من أين تبدأ شركتك في تطبيق الأتمتة؟'),
  ('Choose one task your team repeats.','اختر مهمة يكرّرها فريقك باستمرار.'),
  ('Write down the trigger and the next action.','حدّد ما يبدأ العملية، ثم الخطوة التي تليه.'),
  ('Test it before connecting more steps.','اختبرها قبل ربطها بخطوات إضافية.')]),
 ('Make enquiry forms useful',[
  ('Your enquiry form should make the next step easier.','ينبغي أن يساعد نموذج الاستفسارات على تسهيل الخطوة التالية.'),
  ('Ask only for the details you need.','اطلب البيانات التي تحتاجها فقط.'),
  ('Send the enquiry to the right person.','وجّه الاستفسار إلى الشخص المسؤول عنه.'),
  ('Check that your team receives it.','تأكّد من وصوله إلى فريقك فعلاً.')]),
 ('Keep your pipeline current',[
  ('A pipeline is useful when the information is current.','تكون مراحل البيع مفيدة عندما تكون معلوماتها محدّثة.'),
  ('Update the stage after a real reply.','حدّث المرحلة بعد تلقّي ردّ فعلي.'),
  ('Record the next action and its owner.','سجّل الخطوة التالية والشخص المسؤول عنها.'),
  ('Review what is waiting for attention.','راجع ما ينتظر المتابعة من فريقك.')])]


def script(day):
    title,parts=TOPICS[date.fromisoformat(day).toordinal()%len(TOPICS)]
    parts=parts+[
     ('One Step builds websites, CRM systems, and enquiry automations.','ون ستيب تطوّر المواقع وأنظمة إدارة العملاء وحلول أتمتة الاستفسارات.'),
     ('Message One Step to discuss a practical workflow for your business.','راسل ون ستيب لنناقش سير عمل عملياً يناسب شركتك.')]
    return dict(title=title,fictional_ai_presenter=True,podcast_style=True,minimum_seconds=20,maximum_seconds=30,
                cues=[dict(en=en,ar=ar) for en,ar in parts])
