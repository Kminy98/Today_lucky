import hashlib
import random
from datetime import date, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import FortuneMessage, LuckyOption




def _stable_seed(*parts: str) -> int:
    raw = "|".join(parts).encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return int(digest[:16], 16)


def _parse_birth_date(s: str):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _parse_birth_time(s: str | None) -> str:
    if not s:
        return "00:00"
    datetime.strptime(s, "%H:%M")
    return s


def western_zodiac(d) -> str:
    m, day = d.month, d.day
    if (m == 3 and day >= 21) or (m == 4 and day <= 19): return "Aries"
    if (m == 4 and day >= 20) or (m == 5 and day <= 20): return "Taurus"
    if (m == 5 and day >= 21) or (m == 6 and day <= 20): return "Gemini"
    if (m == 6 and day >= 21) or (m == 7 and day <= 22): return "Cancer"
    if (m == 7 and day >= 23) or (m == 8 and day <= 22): return "Leo"
    if (m == 8 and day >= 23) or (m == 9 and day <= 22): return "Virgo"
    if (m == 9 and day >= 23) or (m == 10 and day <= 22): return "Libra"
    if (m == 10 and day >= 23) or (m == 11 and day <= 21): return "Scorpio"
    if (m == 11 and day >= 22) or (m == 12 and day <= 21): return "Sagittarius"
    if (m == 12 and day >= 22) or (m == 1 and day <= 19): return "Capricorn"
    if (m == 1 and day >= 20) or (m == 2 and day <= 18): return "Aquarius"
    return "Pisces"


def chinese_zodiac(year: int) -> str:
    animals = ["Rat", "Ox", "Tiger", "Rabbit", "Dragon", "Snake",
               "Horse", "Goat", "Monkey", "Rooster", "Dog", "Pig"]
    return animals[(year - 2020) % 12]


ONE_LINERS = {
    "good": [
        "관리자연락요망",
    ],
    "mid": [
        "관리자연락요망",
    ],
    "warn": [
        "관리자연락요망",
    ],
}

LUCKY_COLORS = ["관리자연락요망"]
LUCKY_ITEMS = ["관리자연락요망"]
LUCKY_KEYWORDS = ["관리자연락요망"]


def _score_to_tone(score: int) -> str:
    if score >= 80:
        return "good"
    if score >= 60:
        return "mid"
    return "warn"


@require_GET
def fortune_api(request):
    birth_date_str = request.GET.get("birth_date")
    birth_time_str = request.GET.get("birth_time")  # optional

    if not birth_date_str:
        return JsonResponse({"error": "birth_date is required (YYYY-MM-DD)"}, status=400)

    try:
        bd = _parse_birth_date(birth_date_str)
        bt = _parse_birth_time(birth_time_str)
    except ValueError:
        return JsonResponse({"error": "invalid format. birth_date=YYYY-MM-DD, birth_time=HH:MM"}, status=400)

    today = date.today().isoformat()
    wz = western_zodiac(bd)
    cz = chinese_zodiac(bd.year)

    seed = _stable_seed(birth_date_str, bt, wz, cz, today)
    rng = random.Random(seed)

    score = int(rng.gauss(72, 12))
    score = max(40, min(95, score))
    tone = _score_to_tone(score)

    # tone별 활성 메시지 목록 (DB → fallback)
    msgs = list(
        FortuneMessage.objects
        .filter(tone=tone, is_active=True)
        .values_list("text", flat=True)
    )
    if not msgs:
        msgs = ONE_LINERS[tone]

    colors = list(
        LuckyOption.objects
        .filter(type="color", is_active=True)
        .values_list("value", flat=True)
    )
    items = list(
        LuckyOption.objects
        .filter(type="item", is_active=True)
        .values_list("value", flat=True)
    )
    keywords = list(
        LuckyOption.objects
        .filter(type="keyword", is_active=True)
        .values_list("value", flat=True)
    )

    # DB 비어있을 때 fallback
    if not colors:
        colors = LUCKY_COLORS
    if not items:
        items = LUCKY_ITEMS
    if not keywords:
        keywords = LUCKY_KEYWORDS

    # value 하나씩 뽑기
    color_value = rng.choice(colors)
    item_value = rng.choice(items)
    keyword_value = rng.choice(keywords)


    return JsonResponse(
        {
            "date": today,
            "western_zodiac": wz,
            "chinese_zodiac": cz,
            "score": score,
            "one_line": rng.choice(msgs),
            "lucky": {
                "color": lucky_payload("color", color_value),
                "item": lucky_payload("item", item_value),
                "keyword": lucky_payload("keyword", keyword_value),
            },
        },
        json_dumps_params={"ensure_ascii": False},
    )

def lucky_payload(opt_type: str, value: str | None):
    if not value:
        return {"value": None, "label": None}

    row = (LuckyOption.objects
           .filter(type=opt_type, value=value, is_active=True)
           .values("value", "label")
           .first())

    # 혹시 DB에 없으면 label은 value로 대체(깨짐 방지)
    if not row:
        return {"value": value, "label": value}

    return {
        "value": row["value"],
        "label": row["label"] or row["value"],
    }