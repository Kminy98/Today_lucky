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
        "오늘은 작은 선택 하나가 좋은 흐름을 만들어줘요.",
        "평소보다 운이 가볍게 따라오는 하루예요.",
        "망설였던 일, 오늘은 한 번 움직여봐도 좋아요.",
        "기대하지 않은 곳에서 기분 좋은 일이 생길 수 있어요.",
    ],
    "mid": [
        "큰 변화는 없지만, 안정적인 하루예요.",
        "무리하지 말고 평소 페이스를 유지해보세요.",
        "익숙한 선택이 오히려 도움이 되는 날이에요.",
        "오늘은 차분함이 가장 큰 행운이에요.",
    ],
    "warn": [
        "서두르지 말고 한 번 더 확인해보세요.",
        "작은 말 한마디가 오해로 이어질 수 있어요.",
        "오늘은 쉬어가는 선택도 충분히 의미 있어요.",
        "무리한 계획보다는 컨디션을 우선해 주세요.",
    ],
}

LUCKY_COLORS = [
    {"value": "#2E8B57", "label": "포레스트 그린"},
    {"value": "#FFD700", "label": "골드 옐로우"},
    {"value": "#4F46E5", "label": "딥 인디고"},
    {"value": "#F97316", "label": "소프트 오렌지"},
]

LUCKY_ITEMS = [
    {"value": "mug", "label": "머그컵"},
    {"value": "notebook", "label": "작은 노트"},
    {"value": "earphones", "label": "이어폰"},
    {"value": "keyring", "label": "키링"},
]

LUCKY_KEYWORDS = [
    {"value": "focus", "label": "집중"},
    {"value": "calm", "label": "여유"},
    {"value": "chance", "label": "기회"},
    {"value": "balance", "label": "균형"},
]


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
            "color": lucky_payload("color", rng.choice(colors)),
            "item": lucky_payload("item", rng.choice(items)),
            "keyword": lucky_payload("keyword", rng.choice(keywords)),
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