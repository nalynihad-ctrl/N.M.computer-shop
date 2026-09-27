"""Backend localisation.

The catalogue is stored in English, which stays the single source of truth for
*what exists*: the ``products`` table, the ``category`` column and the payment
and order-status enums are all unchanged, and no migration is required. This
module only translates the *presentation* of those values on the way out.

The API contract is additive. Every endpoint accepts an optional ``lang`` query
parameter (falling back to the ``Accept-Language`` header, then to English), and
when the resolved language is English the responses are byte-for-byte what they
were before this module existed. In every language, responses gain a few extra
*additive* keys and keep every key they already had:

    "category"      the canonical English key - unchanged, so that URLs like
                    /category/GPUs, the ``?category=`` filter and the cart all
                    keep working regardless of the display language
    "categoryName"  the localized name, for rendering
    "status"        the localized status; "statusCode" carries the raw enum
    "name"/"description"/"specs"  localized

Keeping the English key in the URL rather than the localized label is
deliberate: a link shared with someone else has to resolve the same way, and a
localized slug would also need un-translating on the way back in before it
could be used as a query filter.

A key with no translation falls through unchanged, so a product or spec value
added later degrades to English rather than disappearing.
"""

import json
import re

SUPPORTED_LANGUAGES = ("en", "ar", "ku")
DEFAULT_LANGUAGE = "en"

# BCP-47 tags for the Accept-Language parser. Arabic and Kurdish are parsed and
# matched on their primary subtag, so "ckb-IQ", "ku" and "ar-IQ" all resolve.
_BCP47 = {"en": "en", "ar": "ar", "ku": "ku"}


def normalize(value):
    """Reduce a language tag to one of SUPPORTED_LANGUAGES, else None."""
    if not isinstance(value, str):
        return None
    primary = value.strip().lower().replace("_", "-").split("-")[0]
    if primary in _BCP47:
        return primary
    # A couple of tags people actually send for these languages.
    if primary in ("kur", "ckb", "sdh"):
        return "ku"
    return None


def parse_accept_language(header):
    """Order the tags in an ``Accept-Language`` header best-first.

    A tag with no ``q`` is a full preference (1.0). ``q=0`` is an explicit
    refusal, not a weak preference, so it is dropped - sending ``en;q=0,ar``
    means "not English", and treating that as "English" would be the opposite of
    what the client asked for. A malformed ``q`` is likewise not a usable
    preference. Equal qualities keep the order the client sent, which is what
    the grammar asks a server to do.
    """
    if not isinstance(header, str) or not header.strip():
        return []
    ranked = []
    for index, part in enumerate(header.split(",")):
        piece = part.strip()
        if not piece:
            continue
        tag, _, params = piece.partition(";")
        tag = tag.strip()
        if not tag:
            continue
        quality = 1.0
        for param in params.split(";"):
            name, _, value = param.partition("=")
            if name.strip().lower() != "q":
                continue
            try:
                quality = float(value.strip())
            except ValueError:
                quality = 0.0
        if quality <= 0:
            continue
        ranked.append((-quality, index, tag))
    ranked.sort()
    return [tag for _, _, tag in ranked]


def negotiate(header, default=DEFAULT_LANGUAGE):
    """Pick the best language an ``Accept-Language`` header can actually be served in."""
    for tag in parse_accept_language(header):
        if tag == "*":
            # "Any language" is satisfied by the default rather than by
            # whichever happens to sort first.
            return default
        got = normalize(tag)
        if got:
            return got
    return default


def resolve(*candidates):
    """First usable language from ``candidates``, else the default."""
    for candidate in candidates:
        if isinstance(candidate, (list, tuple)):
            for item in candidate:
                got = normalize(item)
                if got:
                    return got
            continue
        got = normalize(candidate)
        if got:
            return got
    return DEFAULT_LANGUAGE


def current_language(args=None, headers=None):
    """Resolve the request language: ``?lang=`` wins, then Accept-Language."""
    from flask import request

    explicit = None
    try:
        explicit = request.args.get("lang")
    except RuntimeError:
        explicit = None
    if explicit is not None:
        # An explicit but unsupported tag is an error in its own right rather
        # than a silent fallback, but it must not 500: normalise it and let the
        # caller fall back to the default.
        return normalize(explicit) or DEFAULT_LANGUAGE
    try:
        header = request.headers.get("Accept-Language", "")
    except RuntimeError:
        header = ""
    return negotiate(header)


def translate(lang, table, key):
    """Look ``key`` up in ``table`` for ``lang``; None if untranslated."""
    if not key or lang == DEFAULT_LANGUAGE:
        return None
    entry = table.get(key)
    if not isinstance(entry, dict):
        return None
    return entry.get(lang)


def t(lang, table, key, default=None):
    """Like :func:`translate` but with a caller-supplied fallback."""
    value = translate(lang, table, key)
    return default if value is None else value


# --------------------------------------------------------------------------
# Categories
# --------------------------------------------------------------------------
CATEGORY_NAMES = {
    "CPUs": {"ar": "معالجات", "ku": "پرۆسێسەرەکان"},
    "GPUs": {"ar": "كروت الشاشة", "ku": "کارتە گرافیکەکان"},
    "Motherboards": {"ar": "اللوحات الأم", "ku": "مۆڵەتە سەرەکییەکان"},
    "RAM": {"ar": "الذاكرة", "ku": "بیرگە"},
    "SSD": {"ar": "الأقراص الصلبة", "ku": "دیسکە ڕەقەکان"},
    "HDD": {"ar": "الأقراص الميكانيكية", "ku": "دیسکە مەکانیکییەکان"},
    "Power Supplies": {"ar": "مزودات الطاقة", "ku": "دابینکەرە کارەبا"},
    "PC Cases": {"ar": "صناديق الحاسوب", "ku": "بۆکسەکان"},
    "Cooling": {"ar": "التبريد", "ku": "ساردکردنەوە"},
    "Monitors": {"ar": "الشاشات", "ku": "مۆنیتەرەکان"},
    "Keyboards": {"ar": "لوحات المفاتيح", "ku": "تەختەکلیلەکان"},
    "Mouse": {"ar": "الفأرة", "ku": "ماوسەکان"},
    "Microphones": {"ar": "الميكروفونات", "ku": "مایکرۆفۆنەکان"},
    "Headsets": {"ar": "سمّاعات الرأس", "ku": "گوێگرەکان"},
    "Laptops": {"ar": "الحواسيب المحمولة", "ku": "لاپتۆپەکان"},
    "Accessories": {"ar": "الملحقات", "ku": "پێداویستییەکان"},
    "Networking": {"ar": "الشبكات", "ku": "تۆڕەکان"},
}


def category_name(lang, name):
    return t(lang, CATEGORY_NAMES, name, name)


# --------------------------------------------------------------------------
# Order status / payment method enums
# --------------------------------------------------------------------------
ORDER_STATUSES = {
    "Pending": {"ar": "قيد الانتظار", "ku": "چاوەڕوانە"},
    "Processing": {"ar": "قيد المعالجة", "ku": "لە پرۆسێسکردندایە"},
    "Shipped": {"ar": "تم الشحن", "ku": "نێردراوە"},
    "Delivered": {"ar": "تم التسليم", "ku": "گەیشت"},
    "Cancelled": {"ar": "ملغى", "ku": "هەڵوەشێنرایەوە"},
    "Refunded": {"ar": "تم الاسترداد", "ku": "پارەیەکی گەڕێندرایەوە"},
}

PAYMENT_METHODS = {
    "Cash on Delivery": {"ar": "الدفع عند الاستلام", "ku": "پارەدان لە کاتی گەیاندن"},
    "Card Payment": {"ar": "الدفع بالبطاقة", "ku": "پارەدان بە کارت"},
}


def order_status(lang, status):
    return t(lang, ORDER_STATUSES, status, status)


def payment_method(lang, method):
    return t(lang, PAYMENT_METHODS, method, method)


# --------------------------------------------------------------------------
# Error messages
# --------------------------------------------------------------------------
# Keyed by the exact English sentence the API already emits, so localising costs
# nothing at the raise site and the English response is untouched. A message
# added later simply falls through in English.
ERRORS = {
    "Product not found": {
        "ar": "المنتج غير موجود",
        "ku": "بەرهەمەکە نەدۆزرایەوە",
    },
    "Not found": {"ar": "غير موجود", "ku": "نەدۆزرایەوە"},
    # Werkzeug's own exception name, used by the HTTP error handler.
    "Not Found": {"ar": "غير موجود", "ku": "نەدۆزرایەوە"},
    "Method Not Allowed": {
        "ar": "طريقة الطلب غير مسموحة",
        "ku": "شێوازی داواکارییەکە ڕێپێدراو نییە",
    },
    "Unauthorized": {"ar": "غير مصرّح", "ku": "ڕێگەپێنەدراو"},
    "Bad Request": {"ar": "طلب غير صالح", "ku": "داواکارییەکە ڕێکەوتاو نییە"},
    "Internal Server Error": {
        "ar": "خطأ داخلي في الخادم",
        "ku": "هەڵەیەکی ناوخۆیی لە سێرڤەر",
    },
    "Not authenticated.": {
        "ar": "لم يتم تسجيل الدخول.",
        "ku": "چوونەژوورەوە نەکراوە.",
    },
    "An account with this email already exists.": {
        "ar": "يوجد حساب بهذا البريد الإلكتروني بالفعل.",
        "ku": "هەژمارێک بەم ئیمەیلە پێشتر هەیە.",
    },
    "Invalid email or password.": {
        "ar": "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
        "ku": "ئیمەیل یان وشە نهێنی هەڵەیە.",
    },
    "Please log in to view your orders.": {
        "ar": "يرجى تسجيل الدخول لعرض طلباتك.",
        "ku": "بۆ بینینی داواکارییەکانت تکایە چوونەژوورەوە بکە.",
    },
    "Order not found.": {"ar": "الطلب غير موجود.", "ku": "داواکارییەکە نەدۆزرایەوە."},
    "minPrice cannot be greater than maxPrice.": {
        "ar": "لا يمكن أن يكون الحد الأدنى للسعر أكبر من الحد الأقصى.",
        "ku": "کەمترین نرخ ناتوانێت لە زۆرترین نرخ گەورەتر بێت.",
    },
    "A product in your cart no longer exists.": {
        "ar": "أحد منتجات سلتك لم يعد موجوداً.",
        "ku": "یەکێک لە بەرهەمەکانی سەبەتەکەت بوونی نییە.",
    },
    "Not enough stock for a product in your cart.": {
        "ar": "الكمية المتوفرة غير كافية لأحد منتجات سلتك.",
        "ku": "بڕی بەردەست بۆ یەکێک لە بەرهەمەکانی سەبەتەکەت کەمە.",
    },
    "Your cart is empty.": {"ar": "سلتك فارغة.", "ku": "سەبەتەکەت بەتاڵەیە."},
    "Request body is too large.": {
        "ar": "حجم الطلب كبير جداً.",
        "ku": "قەبارەی داواکارییەکە زۆر گەورەیە.",
    },
    "Frontend not built yet. Run `npm install && npm run build` inside the frontend folder.": {
        "ar": "لم يُبنَ الواجهة بعد. نفّذ `npm install && npm run build` داخل مجلد الواجهة.",
        "ku": "ڕووکارەکە هێشتا درووست نەکراوە. لە پۆڕێی ڕووکار `npm install && npm run build` بەڕێوەبەرە.",
    },
    "Too many requests. Please try again later.": {
        "ar": "عدد كبير من الطلبات. يرجى المحاولة لاحقاً.",
        "ku": "داواکارییەکی زۆر. تکایە دووبارە هەوڵبدەرەوە.",
    },
}


def error_message(lang, message):
    return t(lang, ERRORS, message, message)


# --------------------------------------------------------------------------
# Validation messages
# --------------------------------------------------------------------------
# Keyed by the *template*, not the rendered sentence, because the rendered form
# embeds a field name and a bound that vary per request. Each translation keeps
# the same number of placeholders in the same order so the captured groups from
# the English sentence can be substituted directly; `tools/check_i18n.py`
# enforces that count. Note the placeholders are spelled `%s` here even where
# the English template uses `%d`: the substituted value is the already-rendered
# text of the bound, so `%s` is both correct and order-tolerant.
VALIDATION_MESSAGES = {
    "Field '%s' must be a string.": {
        "ar": "يجب أن يكون الحقل '%s' نصاً.",
        "ku": "خانەی '%s' دەبێت دەقێکی دەق بنێت.",
    },
    "Field '%s' is required.": {
        "ar": "الحقل '%s' مطلوب.",
        "ku": "خانەی '%s' پێویستە.",
    },
    "Field '%s' must be at least %d characters.": {
        "ar": "يجب أن يكون الحقل '%s' %s حرفاً على الأقل.",
        "ku": "خانەی '%s' دەبێت لانیکەم %s پیت بێت.",
    },
    "Field '%s' must be at most %d characters.": {
        "ar": "يجب ألا يزيد الحقل '%s' عن %s حرف.",
        "ku": "خانەی '%s' دەبێت زۆرتر لە %s پیت نەبێت.",
    },
    "Field '%s' has an invalid format.": {
        "ar": "صيغة الحقل '%s' غير صحيحة.",
        "ku": "فۆرماتی خانەی '%s' هەڵەیە.",
    },
    "Field '%s' must be a valid email address.": {
        "ar": "يجب أن يكون الحقل '%s' بريداً إلكترونياً صالحاً.",
        "ku": "خانەی '%s' دەبێت ناونیشانێکی ئیمەیلی ڕێکەوتاو بنێت.",
    },
    "Field '%s' must be a valid phone number.": {
        "ar": "يجب أن يكون الحقل '%s' رقم هاتف صالحاً.",
        "ku": "خانەی '%s' دەبێت ژمارەی تەلەفۆنێکی ڕێکەوتاو بنێت.",
    },
    "Password must be at least %d characters.": {
        "ar": "يجب أن تكون كلمة المرور %s أحرف على الأقل.",
        "ku": "وشەی نهێنی دەبێت لانیکەم %s پیت بێت.",
    },
    "Password must be at most %d characters.": {
        "ar": "يجب ألا تزيد كلمة المرور عن %s حرف.",
        "ku": "وشەی نهێنی دەبێت زۆرتر لە %s پیت نەبێت.",
    },
    "Field '%s' must be an integer.": {
        "ar": "يجب أن يكون الحقل '%s' عدداً صحيحاً.",
        "ku": "خانەی '%s' دەبێت ژمارەیەکی تەواو بنێت.",
    },
    "Field '%s' must be a whole number.": {
        "ar": "يجب أن يكون الحقل '%s' عدداً صحيحاً بلا كسر.",
        "ku": "خانەی '%s' دەبێت ژمارەیەکی تەواو بێ بەش بێت.",
    },
    "Field '%s' must be a number.": {
        "ar": "يجب أن يكون الحقل '%s' رقماً.",
        "ku": "خانەی '%s' دەبێت ژمارە بنێت.",
    },
    "Field '%s' must be a finite number.": {
        "ar": "يجب أن يكون الحقل '%s' رقماً محدوداً.",
        "ku": "خانەی '%s' دەبێت ژمارەیەکی سنووردار بنێت.",
    },
    "Field '%s' must be greater than or equal to %s.": {
        "ar": "يجب أن يكون الحقل '%s' أكبر من %s أو مساوياً له.",
        "ku": "خانەی '%s' دەبێت گەورەتر یان بەرابەر %s بێت.",
    },
    "Field '%s' must be less than or equal to %s.": {
        "ar": "يجب أن يكون الحقل '%s' أصغر من %s أو مساوياً له.",
        "ku": "خانەی '%s' دەبێت بچووکتر یان بەرابەر %s بێت.",
    },
    "Field '%s' must be one of: %s.": {
        "ar": "يجب أن يكون الحقل '%s' أحد القيم: %s.",
        "ku": "خانەی '%s' دەبێت یەکێک لەم بەهایانە: %s.",
    },
    "Field '%s' must be a boolean.": {
        "ar": "يجب أن يكون الحقل '%s' قيمة منطقية.",
        "ku": "خانەی '%s' دەبێت بەهایەکی بەڵێ/نەخێ بنێت.",
    },
    "Field '%s' is not a valid file name.": {
        "ar": "الحقل '%s' ليس اسم ملف صالحاً.",
        "ku": "خانەی '%s' ناوی فایلێکی ڕێکەوتاو نییە.",
    },
    "Field '%s' accepts at most %d values.": {
        "ar": "يقبل الحقل '%s' %s قيمة كحد أقصى.",
        "ku": "خانەی '%s' زۆرتر لە %s بەها قبوڵ دەکات.",
    },
    "Each value in '%s' must be at most %d characters.": {
        "ar": "يجب ألا تتجاوز كل قيمة في '%s' %s حرف.",
        "ku": "هەر بەهایەک لە '%s' دەبێت زۆرتر لە %s پیت نەبێت.",
    },
    "Content-Type must be application/json.": {
        "ar": "يجب أن يكون نوع المحتوى application/json.",
        "ku": "جۆری ناوەڕۆک دەبێت application/json بێت.",
    },
    "A JSON request body is required.": {
        "ar": "مطلوب جسم طلب بصيغة JSON.",
        "ku": "تەنی داواکارییەکی JSON پێویستە.",
    },
    "Request body must be valid JSON.": {
        "ar": "يجب أن يكون جسم الطلب بصيغة JSON صالحة.",
        "ku": "تەنی داواکارییەکە دەبێت JSONێکی ڕێکەوتاو بنێت.",
    },
    "Request body must be a JSON object.": {
        "ar": "يجب أن يكون جسم الطلب كائن JSON.",
        "ku": "تەنی داواکارییەکە دەبێت شێءیەکی JSON بنێت.",
    },
    "Unexpected field%s: %s.": {
        "ar": "حقل غير متوقع%s: %s.",
        "ku": "خانەی چاوەڕواننەکراو%s: %s.",
    },
    "Field 'items' must be a non-empty array.": {
        "ar": "يجب أن يكون الحقل 'items' مصفوفة غير فارغة.",
        "ku": "خانەی 'items' دەبێت ڕیزێکی بەتاڵ نەبێت.",
    },
    "A maximum of %d items is allowed per order.": {
        "ar": "يُسمح بحد أقصى %s عنصر في كل طلب.",
        "ku": "بۆ هەر داواکارییەک لانیکەم %s بابەت ڕێگەپێدراوە.",
    },
    "Field 'items[%d]' must be an object.": {
        "ar": "يجب أن يكون الحقل 'items[%s]' كائناً.",
        "ku": "خانەی 'items[%s]' دەبێت شێءیەک بنێت.",
    },
}

_PLACEHOLDER = re.compile(r"%[sd]")


def _template_pattern(template):
    """Regex that captures the values substituted into a %-template."""
    out = ["^"]
    index = 0
    while index < len(template):
        if template[index] == "%" and template[index + 1 : index + 2] in ("s", "d"):
            out.append("(.+?)")
            index += 2
            continue
        out.append(re.escape(template[index]))
        index += 1
    out.append("$")
    return re.compile("".join(out), re.DOTALL)


_MATCHERS = None


def _matchers():
    global _MATCHERS
    if _MATCHERS is None:
        _MATCHERS = [
            (template, _template_pattern(template))
            for template in VALIDATION_MESSAGES
        ]
    return _MATCHERS


def validation_message(lang, message):
    """Localise a rendered validation message by matching its template.

    Matching the template rather than the finished sentence is what lets
    validation.py keep raising plain formatted strings: the field name and the
    bound are pulled back out of the sentence and re-inserted into the
    translation. An unrecognised sentence falls through in English.
    """
    if lang == DEFAULT_LANGUAGE or not isinstance(message, str) or not message:
        return message
    for template, pattern in _matchers():
        if not pattern.match(message):
            continue
        translated = VALIDATION_MESSAGES[template].get(lang)
        if not translated:
            continue
        groups = pattern.match(message).groups()
        try:
            return translated % groups
        except (TypeError, ValueError):
            return message
    return message


# --------------------------------------------------------------------------
# Spec labels
# --------------------------------------------------------------------------
# Keys of the ``specs`` JSON object. Values that are pure numbers, units or
# model codes ("12GB GDDR7", "PCIe 5.0 x16", "6000 MT/s", "CL30") are left
# untouched - there is nothing to translate in them - and only the wordy values
# below are mapped.
SPEC_KEYS = {
    "Memory": {"ar": "الذاكرة", "ku": "بیرگە"},
    "Interface": {"ar": "الواجهة", "ku": "ڕووکار"},
    "Ports": {"ar": "المنافذ", "ku": "پۆرتەکان"},
    "Power": {"ar": "القدرة", "ku": "کارەبا"},
    "Warranty": {"ar": "الضمان", "ku": "ضمان"},
    "Cores": {"ar": "الأنوية", "ku": "ناوکەکان"},
    "Base Clock": {"ar": "التردد الأساسي", "ku": "کاتژمێری بنەڕەوە"},
    "Boost Clock": {"ar": "تردد التسريع", "ku": "کاتژمێری بەهێزکردن"},
    "Socket": {"ar": "المقبس", "ku": "بنکە"},
    "TDP": {"ar": "استهلاك الحرارة", "ku": "تەواوی تێمەیی"},
    "Form Factor": {"ar": "شكل القطعة", "ku": "شێوەی دیزاین"},
    "Expansion": {"ar": "التوسعة", "ku": "پەرەپێدان"},
    "Capacity": {"ar": "السعة", "ku": "بەهرە"},
    "Speed": {"ar": "السرعة", "ku": "خێرایی"},
    "Type": {"ar": "النوع", "ku": "جۆر"},
    "Latency": {"ar": "زمن الاستجابة", "ku": "دواخستن"},
    "Read Speed": {"ar": "سرعة القراءة", "ku": "خێرایی خوێندنەوە"},
    "RPM": {"ar": "دورات في الدقيقة", "ku": "خولەکان لە خولەیەکدا"},
    "Wattage": {"ar": "القدرة", "ku": "توانا"},
    "Efficiency": {"ar": "الكفاءة", "ku": "کارایی"},
    "Modular": {"ar": "نوع التوصيل", "ku": "جۆری پەیوەندی"},
    "Fan": {"ar": "المروحة", "ku": "پەنکە"},
    "Motherboard": {"ar": "اللوحة الأم", "ku": "مۆڵەتی سەرەکی"},
    "GPU Clearance": {"ar": "مساحة كرت الشاشة", "ku": "بۆشایی کارتی گرافیک"},
    "Side Panel": {"ar": "اللوح الجانبي", "ku": "پانێڵی لاوەکی"},
    "Height": {"ar": "الارتفاع", "ku": "بەرزی"},
    "Fans": {"ar": "المراوح", "ku": "پەنکەکان"},
    "Radiator": {"ar": "المبرّد المائي", "ku": "ڕادیەتەر"},
    "Size": {"ar": "الحجم", "ku": "قەبارە"},
    "Resolution": {"ar": "الدقة", "ku": "ڕوونی"},
    "Refresh Rate": {"ar": "معدل التحديث", "ku": "خێرایی نوێبوونەوە"},
    "Panel": {"ar": "اللوح", "ku": "پانێڵ"},
    "Layout": {"ar": "التخطيط", "ku": "ڕووکار"},
    "Switch": {"ar": "المفتاح", "ku": "سویچ"},
    "Connection": {"ar": "الاتصال", "ku": "پەیوەندی"},
    "Backlight": {"ar": "الإضاءة الخلفية", "ku": "ڕووناکی پاش"},
    "Sensor": {"ar": "المستشعر", "ku": "هەستێنەر"},
    "DPI": {"ar": "الدقة", "ku": "ڕوونی"},
    "Buttons": {"ar": "الأزرار", "ku": "دوگمەکان"},
    "Polar Pattern": {"ar": "النمط القطبي", "ku": "نەخشی قەطبی"},
    "Frequency Response": {"ar": "استجابة التردد", "ku": "کاتژمێری کاتژمێر"},
    "Bit Depth": {"ar": "عمق البت", "ku": "قووڕی بیت"},
    "Driver": {"ar": "المشغّل", "ku": "دایکەر"},
    "Battery": {"ar": "البطارية", "ku": "باتری"},
    "Microphone": {"ar": "الميكروفون", "ku": "مایکرۆفۆن"},
    "CPU": {"ar": "المعالج", "ku": "پرۆسێسەر"},
    "GPU": {"ar": "كرت الشاشة", "ku": "کارتی گرافیک"},
    "RAM": {"ar": "الذاكرة", "ku": "بیرگە"},
    "Storage": {"ar": "التخزين", "ku": "هەڵگرتن"},
    "Display": {"ar": "الشاشة", "ku": "شاشە"},
    "Video": {"ar": "الفيديو", "ku": "ڤیدیۆ"},
    "Power Delivery": {"ar": "توصيل الطاقة", "ku": "گەیاندنی کارەبا"},
    "Frame Rate": {"ar": "معدل الإطارات", "ku": "خێرایی فرەیم"},
    "Amount": {"ar": "الكمية", "ku": "بڕ"},
    "Conductivity": {"ar": "التوصيل الحراري", "ku": "گەیاندنی گەرمی"},
    "Viscosity": {"ar": "اللزوجة", "ku": "ڕووتی"},
    "Shelf Life": {"ar": "مدة الصلاحية", "ku": "ماوەی بەکارهێنان"},
    "Surface": {"ar": "السطح", "ku": "ڕووکار"},
    "Base": {"ar": "القاعدة", "ku": "بنەڕەوە"},
    "Lighting": {"ar": "الإضاءة", "ku": "ڕووناکی"},
    "Standard": {"ar": "المعيار", "ku": "ستاندارد"},
    "Bands": {"ar": "النطاقات", "ku": "باندەکان"},
}

SPEC_VALUES = {
    "1 Year": {"ar": "سنة واحدة", "ku": "یەک ساڵ"},
    "2 Years": {"ar": "سنتان", "ku": "دوو ساڵ"},
    "3 Years": {"ar": "٣ سنوات", "ku": "سێ ساڵ"},
    "5 Years": {"ar": "٥ سنوات", "ku": "پێنج ساڵ"},
    "6 Years": {"ar": "٦ سنوات", "ku": "شەش ساڵ"},
    "10 Years": {"ar": "١٠ سنوات", "ku": "دە ساڵ"},
    "Lifetime": {"ar": "مدى الحياة", "ku": "هەمیشە"},
    "N/A": {"ar": "لا ينطبق", "ku": "گەڕەنەوە"},
    "Fully Modular": {"ar": "قابل للفصل بالكامل", "ku": "بە تەواوی مۆدیۆۆلار"},
    "Semi Modular": {"ar": "شبه قابل للفصل", "ku": "نیوە مۆدیۆۆلار"},
    "Wired": {"ar": "سلكي", "ku": "وایەرد"},
    "Wireless": {"ar": "لاسلكي", "ku": "بێ وایەر"},
    "Tempered Glass": {"ar": "زجاج مقوّى", "ku": "چووشکاری بەهێزکراو"},
    "Mid Tower": {"ar": "برج متوسط", "ku": "تاوی مامناوەند"},
    "Air Cooler": {"ar": "مبرّد هوائي", "ku": "ساردکەری هەوا"},
    "Liquid Cooler": {"ar": "مبرّد مائي", "ku": "ساردکەری ئاو"},
    "Cardioid": {"ar": "قلبي", "ku": "دڵی"},
    "Supercardioid": {"ar": "شبه قلبي", "ku": "زۆرتر لە دڵی"},
    "4 patterns": {"ar": "٤ أنماط", "ku": "٤ نەخش"},
    "Cloth": {"ar": "قماش", "ku": "شوم"},
    "Non-slip Rubber": {"ar": "مطاط مانع للانزلاق", "ku": "پلاستیکی ڕێکگر لە سڕین"},
    "White LED": {"ar": "LED أبيض", "ku": "LED سپی"},
    "High": {"ar": "عالية", "ku": "بەرز"},
    "Medium": {"ar": "متوسطة", "ku": "مامناوەند"},
    "4x DDR5 up to 128GB": {"ar": "٤× DDR5 حتى ١٢٨ غيغابايت", "ku": "٤× DDR5 تا ١٢٨ گیگابایت"},
    "4x DDR5 up to 192GB": {"ar": "٤× DDR5 حتى ١٩٢ غيغابايت", "ku": "٤× DDR5 تا ١٩٢ گیگابایت"},
    "4K HDMI": {"ar": "HDMI بدقة 4K", "ku": "HDMI بە ڕوونی 4K"},
    "24-bit / 48kHz": {"ar": "٢٤ بت / ٤٨ كيلوهرتز", "ku": "٢٤ بیت / ٤٨ کیلۆهرتز"},
    "20Hz - 20kHz": {"ar": "٢٠ هرتز - ٢٠ كيلوهرتز", "ku": "٢٠ هرتز - ٢٠ کیلۆهرتز"},
    "5400 RPM": {"ar": "٥٤٠٠ لفة/دقيقة", "ku": "٥٤٠٠ خولە لە خولەیەکدا"},
    "7200 RPM": {"ar": "٧٢٠٠ لفة/دقيقة", "ku": "٧٢٠٠ خولە لە خولەیەکدا"},
    "2.5 inch": {"ar": "٢٫٥ بوصة", "ku": "٢٫٥ ئینچ"},
    "3.5 inch": {"ar": "٣٫٥ بوصة", "ku": "٣٫٥ ئینچ"},
    "27 inch": {"ar": "٢٧ بوصة", "ku": "٢٧ ئینچ"},
    "24 inch": {"ar": "٢٤ بوصة", "ku": "٢٤ ئینچ"},
    "32 inch": {"ar": "٣٢ بوصة", "ku": "٣٢ ئینچ"},
    "30fps": {"ar": "٣٠ إطاراً/ثانية", "ku": "٣٠ فرەیم لە چرکەیەکدا"},
    "2.4GHz / Bluetooth": {"ar": "2.4 جيجاهرتز / بلوتوث", "ku": "2.4 گیگاهرتز / بلوتوس"},
    "USB / 3.5mm": {"ar": "USB / 3.5 ملم", "ku": "USB / 3.5 ملم"},
    "USB / XLR": {"ar": "USB / XLR", "ku": "USB / XLR"},
    "USB-C": {"ar": "USB-C", "ku": "USB-C"},
    "USB-A": {"ar": "USB-A", "ku": "USB-A"},
    "Bluetooth / USB-C": {"ar": "بلوتوث / USB-C", "ku": "بلوتوس / USB-C"},
    "240mm": {"ar": "٢٤٠ ملم", "ku": "٢٤٠ ملم"},
    "120mm": {"ar": "١٢٠ ملم", "ku": "١٢٠ ملم"},
    "135mm": {"ar": "١٣٥ ملم", "ku": "١٣٥ ملم"},
    "165mm": {"ar": "١٦٥ ملم", "ku": "١٦٥ ملم"},
    "155mm": {"ar": "١٥٥ ملم", "ku": "١٥٥ ملم"},
    "2x 140mm": {"ar": "٢× ١٤٠ ملم", "ku": "٢× ١٤٠ ملم"},
    "2x 120mm": {"ar": "٢× ١٢٠ ملم", "ku": "٢× ١٢٠ ملم"},
    "365mm": {"ar": "٣٦٥ ملم", "ku": "٣٦٥ ملم"},
    "392mm": {"ar": "٣٩٢ ملم", "ku": "٣٩٢ ملم"},
    "360mm": {"ar": "٣٦٠ ملم", "ku": "٣٦٠ ملم"},
    "900x400mm": {"ar": "٩٠٠×٤٠٠ ملم", "ku": "٩٠٠×٤٠٠ ملم"},
    "850W": {"ar": "٨٥٠ واط", "ku": "٨٥٠ وات"},
    "750W": {"ar": "٧٥٠ واط", "ku": "٧٥٠ وات"},
    "650W": {"ar": "٦٥٠ واط", "ku": "٦٥٠ وات"},
    "250W": {"ar": "٢٥٠ واط", "ku": "٢٥٠ وات"},
    "245W": {"ar": "٢٤٥ واط", "ku": "٢٤٥ وات"},
    "120W": {"ar": "١٢٠ واط", "ku": "١٢٠ وات"},
    "125W": {"ar": "١٢٥ واط", "ku": "١٢٥ وات"},
    "170W": {"ar": "١٧٠ واط", "ku": "١٧٠ وات"},
    "65W": {"ar": "٦٥ واط", "ku": "٦٥ وات"},
    "190W": {"ar": "١٩٠ واط", "ku": "١٩٠ وات"},
    "300W": {"ar": "٣٠٠ واط", "ku": "٣٠٠ وات"},
    "304W": {"ar": "٣٠٤ واط", "ku": "٣٠٤ وات"},
    "360W": {"ar": "٣٦٠ واط", "ku": "٣٦٠ وات"},
    "100W": {"ar": "١٠٠ واط", "ku": "١٠٠ وات"},
    "38 Hours": {"ar": "٣٨ ساعة", "ku": "٣٨ کاتژمێر"},
    "80 PLUS Gold": {"ar": "80 PLUS ذهبي", "ku": "80 PLUS زێڕین"},
    "4x Gigabit LAN": {"ar": "٤× إيثرنت غيغابت", "ku": "٤× پۆرتی LAN گیگابایتی"},
    "ATX / Micro-ATX / ITX": {"ar": "ATX / Micro-ATX / ITX", "ku": "ATX / Micro-ATX / ITX"},
    "E-ATX / ATX / Micro-ATX": {"ar": "E-ATX / ATX / Micro-ATX", "ku": "E-ATX / ATX / Micro-ATX"},
    "AM5 / LGA1700": {"ar": "AM5 / LGA1700", "ku": "AM5 / LGA1700"},
    "Dual Band": {"ar": "نطاقان", "ku": "دوو باند"},
    "Full Size": {"ar": "حجم كامل", "ku": "قەبارەی تەواو"},
    "Dynamic USB/XLR": {"ar": "ديناميكي USB/XLR", "ku": "دینامیکی USB/XLR"},
    "Condenser": {"ar": "مكثّف", "ku": "کۆندانسەر"},
    "Detachable": {"ar": "قابل للفصل", "ku": "لابردەوە"},
    "8": {"ar": "٨", "ku": "٨"},
    "11": {"ar": "١١", "ku": "١١"},
    "5": {"ar": "٥", "ku": "٥"},
    "6": {"ar": "٦", "ku": "٦"},
    "4g": {"ar": "٤ غ", "ku": "٤ گ"},
    "M.2 2280": {"ar": "M.2 2280", "ku": "M.2 2280"},
    "75%": {"ar": "٧٥٪", "ku": "٧٥٪"},
    "8 Years": {"ar": "٨ سنوات", "ku": "هەشت ساڵ"},
    "Stereo": {"ar": "ستيريو", "ku": "ستێریۆ"},
    "BAMF": {"ar": "BAMF (مفتاح خطّي)", "ku": "BAMF (کلیلی هێڵی)"},
    "Chroma RGB": {"ar": "إضاءة Chroma RGB", "ku": "ڕووناکی Chroma RGB"},
    "ClearCast Gen 2": {
        "ar": "تقنية ClearCast من الجيل الثاني",
        "ku": "تەکنەلۆژیای ClearCast نەوەی دووەم",
    },
    "Gateron Brown": {
        "ar": "مفتاح Gateron بنّي اللمس",
        "ku": "کلیلی هەستیاری Gateron قاوەیی",
    },
    "Tactile Brown": {
        "ar": "مفتاح لمسي بنّي",
        "ku": "کلیلی هەستیاری قاوەیی",
    },
    "HyperClear Cardioid": {
        "ar": "التقاط HyperClear قلبي",
        "ku": "لەرگرتنی HyperClear دڵی",
    },
    "Razer Green": {"ar": "أخضر Razer", "ku": "سەوزی Razer"},
}


def localize_specs(lang, specs):
    """Translate the keys and the wordy values of a specs object.

    Purely numeric/unit values miss the table and pass through untouched, which
    is the intended behaviour rather than a gap.
    """
    if lang == DEFAULT_LANGUAGE or not isinstance(specs, dict):
        return specs
    out = {}
    for key, value in specs.items():
        new_key = t(lang, SPEC_KEYS, key, key)
        if isinstance(value, str):
            out[new_key] = t(lang, SPEC_VALUES, value, value)
        else:
            out[new_key] = value
    return out


# --------------------------------------------------------------------------
# Products
# --------------------------------------------------------------------------
# Keyed by the English product name from seed_data._PRODUCTS, which is also what
# the ``products.name`` column holds. A product with no entry here renders its
# English name and description, so a newly seeded product is never blank.
PRODUCTS = {
    "NVIDIA GeForce RTX 5070": {
        "ar": {
            "name": "NVIDIA GeForce RTX 5070",
            "description": "بطاقة RTX 5070 تجلب تتبّع الأشعة من الجيل التالي وتقنية DLSS 4 إلى فئة السعر الشائعة.",
        },
        "ku": {
            "name": "NVIDIA GeForce RTX 5070",
            "description": "کارتی RTX 5070 تەکنەلۆژیای تابڕینی نەوەی داهاتوو و DLSS 4 دەهێنێت بۆ نرخێکی ئاسایی.",
        },
    },
    "NVIDIA GeForce RTX 5080": {
        "ar": {
            "name": "NVIDIA GeForce RTX 5080",
            "description": "أداء ألعاب رائد بمعمارية Blackwell لدقة 4K وشاشات معدّل تحديث مرتفع.",
        },
        "ku": {
            "name": "NVIDIA GeForce RTX 5080",
            "description": "کارایی یاریی پێشەنگ بە تەکنەلۆژیای Blackwell بۆ 4K و شاشەی خێرای نوێبوونەوەی بەرز.",
        },
    },
    "AMD Radeon RX 9070 XT": {
        "ar": {
            "name": "AMD Radeon RX 9070 XT",
            "description": "بطاقة رسوميات بمعمارية RDNA 4 بأداء ممتاز في التظليل و16 غيغابايت من الذاكرة.",
        },
        "ku": {
            "name": "AMD Radeon RX 9070 XT",
            "description": "کارتی گرافیکی تەکنەلۆژیای RDNA 4 بە کارایی زۆر باش لە ڕەسمکردن و ١٦ گیگابایت بیرگە.",
        },
    },
    "Intel Arc B580": {
        "ar": {
            "name": "Intel Arc B580",
            "description": "بطاقة رسوميات اقتصادية للعبة بدقة 1440p مع ترميز AV1 وذاكرة 12 غيغابايت.",
        },
        "ku": {
            "name": "Intel Arc B580",
            "description": "کارتی گرافیکی ئەرزان بۆ یاریی 1440p لەگەڵ کۆدکردنی AV1 و ١٢ گیگابایت بیرگە.",
        },
    },
    "ASUS TUF GeForce RTX 5070 Ti": {
        "ar": {
            "name": "ASUS TUF GeForce RTX 5070 Ti",
            "description": "مكوّنات TUF بمواصفات عسكرية مع ثلاث مراوح بتقنية المحاور ولوح خلفي معدني.",
        },
        "ku": {
            "name": "ASUS TUF GeForce RTX 5070 Ti",
            "description": "پارچەکانی TUF بە پۆلەیەنیی و سێ پەنکەی تەکنەلۆژیای ئەxis و پانێڵێکی دوای ئاسنیی.",
        },
    },
    "AMD Ryzen 7 9800X3D": {
        "ar": {
            "name": "AMD Ryzen 7 9800X3D",
            "description": "بطل الألعاب بلا منازع بذاكرة التخزين المؤقت ثلاثية الأبعاد V-Cache ومعمارية Zen 5.",
        },
        "ku": {
            "name": "AMD Ryzen 7 9800X3D",
            "description": "پاڵەوانی بێ ڕکابەری یارییەکان بە کێشەی V-Cache و تەکنەلۆژیای Zen 5.",
        },
    },
    "Intel Core i9-14900K": {
        "ar": {
            "name": "Intel Core i9-14900K",
            "description": "معالج مكتبي مفتوح بـ24 نواة للألعاب وصناعة المحتوى المكثّف.",
        },
        "ku": {
            "name": "Intel Core i9-14900K",
            "description": "پرۆسێسەری دەسکتۆپی کراوەی ٢٤ ناوک بۆ یاریی زۆر قورس و درووستکردنی ناوەڕۆک.",
        },
    },
    "AMD Ryzen 5 9600X": {
        "ar": {
            "name": "AMD Ryzen 5 9600X",
            "description": "معالج Zen 5 ذكور بـ6 أنوية وكفاءة عالية، مثالي لتجميعات الألعاب متوسطة الفئة.",
        },
        "ku": {
            "name": "AMD Ryzen 5 9600X",
            "description": "پرۆسێسەری Zen 5 یەکەکەم جۆر بە ٦ ناوک و کارایی بەرز، گونجاو بۆ کۆمپیوتەری یاریی مامناوەند.",
        },
    },
    "Intel Core i5-14600K": {
        "ar": {
            "name": "Intel Core i5-14600K",
            "description": "معالج مفتوح بـ14 نواة يقدّم قيمة ممتازة للاعبين وصنّاع المحتوى.",
        },
        "ku": {
            "name": "Intel Core i5-14600K",
            "description": "پرۆسێسەری کراوەی ١٤ ناوک کە بەهایەکی باش بۆ یاریزانان و درووستکەران دەدات.",
        },
    },
    "AMD Ryzen 9 9950X": {
        "ar": {
            "name": "AMD Ryzen 9 9950X",
            "description": "معالج رائد بـ16 نواة للمهام المتعددة الثقيلة والمعالجة والبث المباشر.",
        },
        "ku": {
            "name": "AMD Ryzen 9 9950X",
            "description": "پرۆسێسەری پێشەنگی ١٦ ناوک بۆ کاری چەندووری قورس و ڕەنگکردن و پەخشکردن.",
        },
    },
    "ASUS ROG STRIX B650E-F Gaming": {
        "ar": {
            "name": "ASUS ROG STRIX B650E-F للألعاب",
            "description": "لوحة أم ATX بمقبس AM5 مع PCIe 5.0 وWiFi 6E وتبريد قوي لدائرة تنظيم الجهد.",
        },
        "ku": {
            "name": "ASUS ROG STRIX B650E-F بۆ یاری",
            "description": "مۆڵەتی ATX بە بنکەی AM5 لەگەڵ PCIe 5.0 و WiFi 6E و ساردکردنەوەی بەهێزی VRM.",
        },
    },
    "MSI MAG X670E TOMAHAWK WiFi": {
        "ar": {
            "name": "MSI MAG X670E TOMAHAWK WiFi",
            "description": "لوحة أم AM5 غنية بالمزايا مع PCIe 5.0 M.2 ومشتتات ممتدة.",
        },
        "ku": {
            "name": "MSI MAG X670E TOMAHAWK WiFi",
            "description": "مۆڵەتی AM5 یەکەکەم تایبەتمەندی لەگەڵ M.2 ی PCIe 5.0 و بەشی ساردکردنی درێژ.",
        },
    },
    "Gigabyte Z790 AORUS Elite AX": {
        "ar": {
            "name": "Gigabyte Z790 AORUS Elite AX",
            "description": "لوحة أم بمقبس LGA1700 تدعم DDR5 مع شبكة 2.5GbE.",
        },
        "ku": {
            "name": "Gigabyte Z790 AORUS Elite AX",
            "description": "مۆڵەتی LGA1700 پشتگیری DDRە بە هەمرە تۆڕی 2.5GbE.",
        },
    },
    "ASRock B760M Pro RS": {
        "ar": {
            "name": "ASRock B760M Pro RS",
            "description": "لوحة أم مدمجة بمقاس micro-ATX مع DDR5 وPCIe 4.0 لتجميعات اقتصادية.",
        },
        "ku": {
            "name": "ASRock B760M Pro RS",
            "description": "مۆڵەتی میکرۆ-ATX پاشکەوتکراو بە DDRە و PCIe 4.0 بۆ کۆمپیوتەری ئەرزان.",
        },
    },
    "Corsair Vengeance 32GB DDR5-6000": {
        "ar": {
            "name": "Corsair Vengeance 32GB DDR5-6000",
            "description": "طقم ذاكرة DDR5 منخفض الارتفاع بتوقيتات محكمة ودعم AMD EXPO.",
        },
        "ku": {
            "name": "Corsair Vengeance 32GB DDR5-6000",
            "description": "کۆمەڵەی بیرگەی DDR5 بەرزی کەم بە کاتژمێری توند و پشتگیری AMD EXPO.",
        },
    },
    "G.Skill Trident Z5 RGB 32GB DDR5-6400": {
        "ar": {
            "name": "G.Skill Trident Z5 RGB 32GB DDR5-6400",
            "description": "طقم ذاكرة RGB فاخر مضبوط لمنصات Intel XMP 3.0.",
        },
        "ku": {
            "name": "G.Skill Trident Z5 RGB 32GB DDR5-6400",
            "description": "کۆمەڵەی بیرگەی RGB پێشەنگ کە بۆ پلاتفۆرمەکانی Intel XMP 3.0 ڕێکخراوە.",
        },
    },
    "Kingston Fury Beast 16GB DDR4-3200": {
        "ar": {
            "name": "Kingston Fury Beast 16GB DDR4-3200",
            "description": "ترقية DDR4 موثوقة تعمل فوراً للأنظمة القديمة.",
        },
        "ku": {
            "name": "Kingston Fury Beast 16GB DDR4-3200",
            "description": "نوێکردنەوەی DDRێکی پشتگیرکراو کە بۆ سیستەمە کۆنەکان ئامادەیە.",
        },
    },
    "Crucial Pro 64GB DDR5-5600": {
        "ar": {
            "name": "Crucial Pro 64GB DDR5-5600",
            "description": "طقم ذاكرة DDR5 عالي السعة لأجهزة العمل والمهام المتعددة الثقيلة.",
        },
        "ku": {
            "name": "Crucial Pro 64GB DDR5-5600",
            "description": "کۆمەڵەی بیرگەی DDR5 بە بەهرەی بەرز بۆ ئامێری کاری و کاری چەندووری.",
        },
    },
    "Samsung 990 PRO 2TB NVMe": {
        "ar": {
            "name": "Samsung 990 PRO 2TB NVMe",
            "description": "قرص NVMe بواجهة PCIe 4.0 يوفّر سرعة قراءة متتابعة تصل إلى 7450 ميجابايت/ثانية.",
        },
        "ku": {
            "name": "Samsung 990 PRO 2TB NVMe",
            "description": "دیسکی NVMe بە ڕووکاری PCIe 4.0 کە خێرایی خوێندنەوەی یەکلێنی تا ٧٤٥٠ مێگابایت لە چرکەیەکدا دەدات.",
        },
    },
    "WD_BLACK SN850X 1TB": {
        "ar": {
            "name": "WD_BLACK SN850X 1TB",
            "description": "قرص NVMe موجّه للألعاب مع وضع Game Mode 2.0 وزمن استجابة منخفض.",
        },
        "ku": {
            "name": "WD_BLACK SN850X 1TB",
            "description": "دیسکی NVMe یاریی لەگەڵ دۆخی Game Mode 2.0 و دواخستنی کەم.",
        },
    },
    "Crucial P3 Plus 1TB": {
        "ar": {
            "name": "Crucial P3 Plus 1TB",
            "description": "تخزين NVMe بواجهة PCIe 4.0 بسعر مناسب للمستخدم اليومي.",
        },
        "ku": {
            "name": "Crucial P3 Plus 1TB",
            "description": "شوێنی هەڵگرتنی NVMe بە ڕووکاری PCIe 4.0 بە نرخێکی گونجاو بۆ بەکارهێنەری ڕۆژانە.",
        },
    },
    "Samsung 870 EVO 1TB SATA": {
        "ar": {
            "name": "Samsung 870 EVO 1TB SATA",
            "description": "قرص SATA مجرّب للحواسيب المحمولة والمكتبية ذات الفتحات مقاس 2.5 بوصة.",
        },
        "ku": {
            "name": "Samsung 870 EVO 1TB SATA",
            "description": "دیسکی SATA ی پشتژووکراو بۆ لاپتۆپ و دەسکتۆپ بە بۆشای ٢٫٥ ئینچ.",
        },
    },
    "Seagate BarraCuda 4TB": {
        "ar": {
            "name": "Seagate BarraCuda 4TB",
            "description": "قرص صلب كبير السعة مقاس 3.5 بوصة للتخزين الواسع.",
        },
        "ku": {
            "name": "Seagate BarraCuda 4TB",
            "description": "دیسکی ڕەقی بە بەهرەی بەرزی ٣٫٥ ئینچ بۆ شوێنی هەڵگرتنی زۆر.",
        },
    },
    "WD Blue 2TB": {
        "ar": {
            "name": "WD Blue 2TB",
            "description": "قرص تخزين موثوق للاستخدام اليومي باستهلاك طاقة منخفض.",
        },
        "ku": {
            "name": "WD Blue 2TB",
            "description": "دیسکی هەڵگرتنی پشتگیرکراو بۆ بەکارهێنانی ڕۆژانە بە تەواوی کارەبای کەم.",
        },
    },
    "Seagate IronWolf 8TB NAS": {
        "ar": {
            "name": "Seagate IronWolf 8TB NAS",
            "description": "قرص مخصص لأجهزة NAS بتحمّل اهتزاز وحدات التخزين المتعددة.",
        },
        "ku": {
            "name": "Seagate IronWolf 8TB NAS",
            "description": "دیسکی تایبەت بۆ NAS کە لە لەشاندنی چەند دیسکیدا تەواوە.",
        },
    },
    "Corsair RM850x 850W Gold": {
        "ar": {
            "name": "Corsair RM850x 850W Gold",
            "description": "وحدة طاقة بشهادة 80 PLUS Gold قابلة للفصل بالكامل مع وضع صامت بلا مروحة.",
        },
        "ku": {
            "name": "Corsair RM850x 850W Gold",
            "description": "دابینکەرێکی 80 PLUS زێڕین بە تەواوی مۆدیۆۆلار لەگەڵ دۆخی بێدەنگ بێ پەنکە.",
        },
    },
    "EVGA 650 GQ 650W Gold": {
        "ar": {
            "name": "EVGA 650 GQ 650W Gold",
            "description": "وحدة طاقة موثوقة شبه قابلة للفصل لتجميعات الألعاب السائدة.",
        },
        "ku": {
            "name": "EVGA 650 GQ 650W Gold",
            "description": "دابینکەرێکی پشتگیرکراوی نیوە مۆدیۆۆلار بۆ کۆمپیوتەری یاریی ئاسایی.",
        },
    },
    "Seasonic FOCUS GX-750": {
        "ar": {
            "name": "Seasonic FOCUS GX-750",
            "description": "وحدة طاقة مدمجة جاهزة لمعيار ATX 3.0 مع ممتازة في كبح التذبذب.",
        },
        "ku": {
            "name": "Seasonic FOCUS GX-750",
            "description": "دابینکەرێکی پاشکەوتکراوی ئامادە بۆ ATX 3.0 لەگەڵ کۆنتڕۆڵی بەرز لە نەشت.",
        },
    },
    "NZXT H5 Flow": {
        "ar": {
            "name": "NZXT H5 Flow",
            "description": "علبة برج متوسطة مُحسّنة لتدفق الهواء مع قناة نظيفة لإدارة الكابلات.",
        },
        "ku": {
            "name": "NZXT H5 Flow",
            "description": "بۆکسی تاوی مامناوەند باشکراو بۆ ڕێژەی هەوا لەگەڵ کەناڵێکی پاک بۆ ڕێکخستنی وایەر.",
        },
    },
    "Lian Li Lancool 216": {
        "ar": {
            "name": "Lian Li Lancool 216",
            "description": "علبة بتدفق هوائي عالٍ مع مراوح أمامية ARGB مقاس 160 مم مدمجة.",
        },
        "ku": {
            "name": "Lian Li Lancool 216",
            "description": "بۆکسی بە ڕێژەی هەوای بەرز لەگەڵ دوو پەنکەی پێشەوەی ARGB ی ١٦٠ ملم.",
        },
    },
    "Corsair 4000D Airflow": {
        "ar": {
            "name": "Corsair 4000D Airflow",
            "description": "علبة نظيفة سهلة البناء بلوحة أمامية عالية النفاذية للهواء.",
        },
        "ku": {
            "name": "Corsair 4000D Airflow",
            "description": "بۆکسێکی پاک و ئاسان بۆ چاندن لەگەڵ پانێڵی پێشەوەی ڕێژەی هەوای بەرز.",
        },
    },
    "Noctua NH-D15": {
        "ar": {
            "name": "Noctua NH-D15",
            "description": "مبرّد هوائي ببرجين بأداء صامت أسطوري.",
        },
        "ku": {
            "name": "Noctua NH-D15",
            "description": "ساردکەری هەوای دوو تاوی بە کارایی بێدەنگی ئەفسانەیی.",
        },
    },
    "NZXT Kraken 240 AIO": {
        "ar": {
            "name": "NZXT Kraken 240 AIO",
            "description": "مبرّد مائي مقاس 240 مم مع شاشة LCD ومضخة صامتة.",
        },
        "ku": {
            "name": "NZXT Kraken 240 AIO",
            "description": "ساردکەری ئاوی ٢٤٠ ملم بە شاشەی LCD و پمپی بێدەنگ.",
        },
    },
    "Thermalright Peerless Assassin 120": {
        "ar": {
            "name": "Thermalright Peerless Assassin 120",
            "description": "مبرّد اقتصادي ممتاز ببرجين وبقيمة رائعة.",
        },
        "ku": {
            "name": "Thermalright Peerless Assassin 120",
            "description": "ساردکەری دوو تاوی بەرهەمی ئەرزانی زۆر باش.",
        },
    },
    'LG UltraGear 27GP850 27"': {
        "ar": {
            "name": 'شاشة LG UltraGear 27GP850 27" للألعاب',
            "description": "شاشة ألعاب QHD مقاس 27 بوصة بدقة 165 هرتز واستجابة 1 مللي ثانية.",
        },
        "ku": {
            "name": 'مۆنیتەری یاریی LG UltraGear 27GP850 27"',
            "description": "مۆنیتەری یاریی QHD ی ٢٧ ئینچ بە ١٦٥ هرتز و کاتژمێری ١ میلی چرکە.",
        },
    },
    'Samsung Odyssey G5 32"': {
        "ar": {
            "name": 'شاشة Samsung Odyssey G5 32" منحنية',
            "description": "لوحة منحنيةimmersive بدقة 1000R وبجودة QHD للألعاب والعمل.",
        },
        "ku": {
            "name": 'مۆنیتەری خڕی Samsung Odyssey G5 32"',
            "description": "پانێڵی خڕی ١٠٠٠R بە کوالێتی QHD بۆ یاری و کار.",
        },
    },
    'Dell S2421HGF 24"': {
        "ar": {
            "name": 'شاشة Dell S2421HGF 24" للألعاب',
            "description": "شاشة ألعاب بدقة Full HD ومعدل تحديث 144 هرتز بإطار نحيف.",
        },
        "ku": {
            "name": 'مۆنیتەری یاریی Dell S2421HGF 24"',
            "description": "مۆنیتەری یاریی Full HD بە ١٤٤ هرتز و چوارچێووی ناسک.",
        },
    },
    "Keychron K8 Pro Wireless": {
        "ar": {
            "name": "Keychron K8 Pro لاسلكي",
            "description": "لوحة مفاتيح ميكانيكية بمقاس 75% قابلة لتبديل المفاتيح مع دعم QMK/VIA.",
        },
        "ku": {
            "name": "Keychron K8 Pro بێ وایەر",
            "description": "تەختەکلیلی میکانیکی ٧٥٪ کە کلیلەکانی گۆڕانە و پشتگیری QMK/VIA دەکات.",
        },
    },
    "Razer BlackWidow V4": {
        "ar": {
            "name": "Razer BlackWidow V4",
            "description": "لوحة مفاتيح ميكانيكية كاملة الحجم بمفاتيح ماكرو مخصّصة.",
        },
        "ku": {
            "name": "Razer BlackWidow V4",
            "description": "تەختەکلیلی میکانیکی قەبارەی تەواو بە کلیلی ماکرۆی تایبەت.",
        },
    },
    "Logitech G413 SE": {
        "ar": {
            "name": "Logitech G413 SE",
            "description": "لوحة مفاتيح ميكانيكية سلكية متينة بأغطية مفاتيح من البلاستيك PBT.",
        },
        "ku": {
            "name": "Logitech G413 SE",
            "description": "تەختەکلیلی میکانیکی وایەردی بەهێز بە دراوبەشی کلیلی PBT.",
        },
    },
    "Logitech G502 HERO": {
        "ar": {
            "name": "Logitech G502 HERO",
            "description": "فأرة ألعاب أيقونية بمستشعر HERO 25K وأوزان قابلة للضبط.",
        },
        "ku": {
            "name": "Logitech G502 HERO",
            "description": "ماوسی یاریی ئایکۆنیک بە هەستێنەری HERO 25K و کێشی ڕێکپێدراو.",
        },
    },
    "Razer DeathAdder V3": {
        "ar": {
            "name": "Razer DeathAdder V3",
            "description": "فأرة خفيفة الوزن ومريحة بمستشعر Focus Pro 30K.",
        },
        "ku": {
            "name": "Razer DeathAdder V3",
            "description": "ماوسێکی سووک و ئەرەگۆنۆمیک بە هەستێنەری Focus Pro 30K.",
        },
    },
    "Glorious Model O Wireless": {
        "ar": {
            "name": "Glorious Model O لاسلكي",
            "description": "فأرة لاسلكية بهيكل شبكي weighs لا تتجاوز 69 غراماً.",
        },
        "ku": {
            "name": "Glorious Model O بێ وایەر",
            "description": "ماوسێکی بێ وایەر بە پانێڵی هەڵتەوە کە تەنها ٦٩ گرامە.",
        },
    },
    "Shure MV7 USB Podcast Mic": {
        "ar": {
            "name": "ميكروفون بودكاست Shure MV7 بمنفذ USB",
            "description": "ميكروفون بودكاست ديناميكي بمنفذي USB/XLR مع معالجة إشارة رقمية وواجهة صوت مدمجة.",
        },
        "ku": {
            "name": "مایکرۆفۆنی پۆدکاستی شۆر MV7 بە USB",
            "description": "مایکرۆفۆنی پۆدکاستی دینامیکی بە USB/XLR لەگەڵ DSP و ڕووکاری دەنگی ناوخۆیی.",
        },
    },
    "Blue Yeti X USB Mic": {
        "ar": {
            "name": "ميكروفون Blue Yeti X بمنفذ USB",
            "description": "ميكروفون مكثّف احترافي بأربع كبسولات ومؤشر مستوى صوتي بالـLED.",
        },
        "ku": {
            "name": "مایکرۆفۆنی Blue Yeti X بە USB",
            "description": "مایکرۆفۆنی کۆندانسەری پیشەیی چوار کەپسوولی لەگەڵ پێشاندانی ئاست بە LED.",
        },
    },
    "Audio-Technica AT2020": {
        "ar": {
            "name": "Audio-Technica AT2020",
            "description": "ميكروفون مكثّف بمستوى استوديو للأصوات والآلات الموسيقية.",
        },
        "ku": {
            "name": "Audio-Technica AT2020",
            "description": "مایکرۆفۆنی کۆندانسەری ئاستی ستۆدیۆ بۆ دەنگ و ئامێری مۆسیقا.",
        },
    },
    "Razer Seiren V2 X": {
        "ar": {
            "name": "Razer Seiren V2 X",
            "description": "ميكروفون بث مباشر مدمج مع التقاط قلبي فائق ومنفذ USB-C.",
        },
        "ku": {
            "name": "Razer Seiren V2 X",
            "description": "مایکرۆفۆنی پەخشکردنی پاشکەوتکراو بە لەرگرتنی زۆرتر لە دڵ و USB-C.",
        },
    },
    "HyperX QuadCast S": {
        "ar": {
            "name": "HyperX QuadCast S",
            "description": "ميكروفون مكثّف بإضاءة RGB مع حامل مانع للاهتزاز وإمكانية الكتم باللمس.",
        },
        "ku": {
            "name": "HyperX QuadCast S",
            "description": "مایکرۆفۆنی کۆندانسەری RGB بە گرتنەڕێی دژە لەشاندن و بی‌دەنگکردن بە دەست.",
        },
    },
    "SteelSeries Arctis Nova 7": {
        "ar": {
            "name": "SteelSeries Arctis Nova 7",
            "description": "سمّاعة رأس لاسلكية متعددة المنصات بصوت محيطي 360 درجة.",
        },
        "ku": {
            "name": "SteelSeries Arctis Nova 7",
            "description": "گوێگرێکی سەرەکی بێ وایەر بۆ چەند پلاتفۆرم لەگەڵ دەنگی دەوری ٣٦٠.",
        },
    },
    "HyperX Cloud II": {
        "ar": {
            "name": "HyperX Cloud II",
            "description": "سمّاعة ألعاب مريحة بصوت محيطي افتراضي 7.1.",
        },
        "ku": {
            "name": "HyperX Cloud II",
            "description": "گوێگرێکی یاریی ئاسودە بە دەنگی دەوری ٧٫١ نەخشی.",
        },
    },
    "Razer BlackShark V2": {
        "ar": {
            "name": "Razer BlackShark V2",
            "description": "سمّاعة رياضات إلكترونية خفيفة الوزن بمشغّلات تيتانيوم TriForce.",
        },
        "ku": {
            "name": "Razer BlackShark V2",
            "description": "گوێگرێکی یارییەکانی ئەلیکترۆنی سووک بە دایکەری تیتانیۆم TriForce.",
        },
    },
    "ASUS ROG Zephyrus G14": {
        "ar": {
            "name": "حاسوب ASUS ROG Zephyrus G14 للألعاب",
            "description": "حاسوب ألعاب مقاس 14 بوصة بشاشة QHD بتردد 165 هرتز وبطاقة رسوميات RTX.",
        },
        "ku": {
            "name": "لاپتۆپی یاریی ASUS ROG Zephyrus G14",
            "description": "لاپتۆپی یاریی ١٤ ئینچ بە شاشەی QHD ی ١٦٥ هرتز و کارتی گرافیکی RTX.",
        },
    },
    "Lenovo Legion 5 Pro": {
        "ar": {
            "name": "Lenovo Legion 5 Pro للألعاب",
            "description": "حاسوب ألعاب مقاس 16 بوصة بلوحة WQXGA ساطعة بسطوع 500-nit.",
        },
        "ku": {
            "name": "لاپتۆپی یاریی Lenovo Legion 5 Pro",
            "description": "لاپتۆپی یاریی ١٦ ئینچ بە پانێڵی WQXGA ڕووناک بە ٥٠٠ نیت.",
        },
    },
    "Acer Nitro V 15": {
        "ar": {
            "name": "Acer Nitro V 15 للألعاب",
            "description": "حاسوب ألعاب اقتصادي يقدّم قيمة رائعة للعبة بدقة 1080p.",
        },
        "ku": {
            "name": "لاپتۆپی یاریی Acer Nitro V 15",
            "description": "لاپتۆپی یاریی سەرەتایی بەهایەکی باش بۆ یاریی 1080p دەدات.",
        },
    },
    "USB-C Docking Hub 8-in-1": {
        "ar": {
            "name": "موصّل USB-C متعدد المنافذ 8 في 1",
            "description": "موصّل من الألومنيوم بمنافذ HDMI وUSB-A وبطاقة SD وشحن بقدرة 100 واط.",
        },
        "ku": {
            "name": "یۆچکەری USB-C بە ٨ پۆرت لە یەکدا",
            "description": "یۆچکەرێکی ئەلیۆمینی بە HDMI و USB-A و کارتی SD و گەیاندنی کارەبای ١٠٠ وات.",
        },
    },
    "Logitech C920 HD Webcam": {
        "ar": {
            "name": "كاميرا لوجيتك C920 HD",
            "description": "كاميرا ويب بدقة Full HD 1080p مع ميكروفونين للمكالمات الواضحة.",
        },
        "ku": {
            "name": "کامێرای وێبی لۆجیتیک C920 HD",
            "description": "کامێرای وێبی بە ڕوونی Full HD ی 1080p لەگەڵ دوو مایکرۆفۆن بۆ بانگی ڕوون.",
        },
    },
    "Arctic MX-6 Thermal Paste": {
        "ar": {
            "name": "معجون تبريد Arctic MX-6",
            "description": "معجون حراري عالي الأداء سهل الفرد طويل العمر.",
        },
        "ku": {
            "name": "مەیندەی ساردکردنەوەی Arctic MX-6",
            "description": "مەیندەی گەرمی بەکارایی بەرز کە بە ئاسانی پێش دەگرێت و ماوەی درێژی هەیە.",
        },
    },
    "RGB Gaming Mousepad XL": {
        "ar": {
            "name": "لوحة فأرة ألعاب RGB بحجم XL",
            "description": "لوحة فأرة قماشية ممتدة بسطح ناعم منخفض الاحتكاك.",
        },
        "ku": {
            "name": "پەڕەی ماوسی یاریی RGB قەبارەی XL",
            "description": "پەڕەی ماوسی شومی درێژ بە ڕووکارێکی نەرم و لەبەرگرتنی کەم.",
        },
    },
    "TP-Link Archer AX73 WiFi 6": {
        "ar": {
            "name": "راوتر TP-Link Archer AX73 WiFi 6",
            "description": "راوتر WiFi 6 ثنائي النطاق بمجموع سرعة 5400 ميغابت/ثانية.",
        },
        "ku": {
            "name": "ڕۆتەری TP-Link Archer AX73 WiFi 6",
            "description": "ڕۆتەری WiFi 6 دوو باند بە کۆی خێرایی ٥٤٠٠ مێگابایت لە چرکەیەکدا.",
        },
    },
    "NETGEAR Nighthawk AX5400": {
        "ar": {
            "name": "راوتر NETGEAR Nighthawk AX5400",
            "description": "راوتر WiFi 6 عالي الأداء للمنازل الكبيرة ولاعبي الألعاب.",
        },
        "ku": {
            "name": "ڕۆتەری NETGEAR Nighthawk AX5400",
            "description": "ڕۆتەری WiFi 6 بە کارایی بەرز بۆ ماڵە گەورەکان و یاریزانان.",
        },
    },
}


def product_text(lang, name, description):
    """Return (localized name, localized description) for a product.

    Falls back to the stored English for either field independently, so a
    translation that covers only the description still gets a translated one.
    """
    entry = PRODUCTS.get(name)
    if not entry or lang == DEFAULT_LANGUAGE:
        return name, description
    tr = entry.get(lang) or {}
    return tr.get("name", name), tr.get("description", description)


# --------------------------------------------------------------------------
# Localized search
# --------------------------------------------------------------------------
def localized_matches(lang, rows, needle):
    """Ids of ``rows`` whose Arabic/Kurdish text contains ``needle``.

    The SQL search runs against the English columns, so a shopper typing an
    Arabic or Kurdish word would otherwise get nothing back. This is a
    compensating scan over the translated text.

    It is a full pass over the candidate rows, which is fine for a catalogue
    of this size and is deliberately bounded by the caller; a table with real
    inventory would want translated columns and a full-text index instead,
    rather than this scan.
    """
    if lang == DEFAULT_LANGUAGE or not needle:
        return []
    low = needle.lower()
    hits = []
    for row in rows:
        name, desc = product_text(lang, row["name"], row["description"])
        # The category is matched in its translated form too, so searching for
        # the word a shopper would use for the category ("mouse", "فأرة") finds
        # the products in it. The raw English column is kept in the haystack as
        # well so model numbers stay searchable.
        #
        # Specs are the bulk of what distinguishes one part from another, so
        # searching "PCIe" or "16 GB" has to work as well as searching a name.
        # The column holds English JSON, so it is parsed and run through the same
        # translator the serializer uses; the raw text is kept too so a model
        # number inside a spec ("DDR5-6000") is still findable in any language.
        specs_text = []
        raw_specs = row.get("specs")
        if isinstance(raw_specs, str):
            try:
                parsed = json.loads(raw_specs)
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, dict):
                specs_text.append(raw_specs)
                for key, value in localize_specs(lang, parsed).items():
                    specs_text.append(str(key))
                    specs_text.append(str(value))
            else:
                specs_text.append(raw_specs)
        elif isinstance(raw_specs, dict):
            specs_text.append(json.dumps(raw_specs, ensure_ascii=False))
            for key, value in localize_specs(lang, raw_specs).items():
                specs_text.append(str(key))
                specs_text.append(str(value))
        haystack = " ".join(
            [
                name,
                desc,
                row.get("brand") or "",
                row.get("category") or "",
                category_name(lang, row.get("category") or ""),
                " ".join(specs_text),
            ]
        ).lower()
        if low in haystack:
            hits.append(int(row["id"]))
    return hits

