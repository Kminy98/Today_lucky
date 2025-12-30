from django.db import models


class FortuneMessage(models.Model):
    TONE_GOOD = "good"
    TONE_MID = "mid"
    TONE_WARN = "warn"

    TONE_CHOICES = [
        (TONE_GOOD, "좋음"),
        (TONE_MID, "보통"),
        (TONE_WARN, "주의"),
    ]

    tone = models.CharField(max_length=10, choices=TONE_CHOICES, verbose_name="톤")
    text = models.CharField(max_length=200, verbose_name="운세 문구")
    is_active = models.BooleanField(default=True, verbose_name="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "운세 문구"
        verbose_name_plural = "운세 문구"

    def __str__(self):
        # get_tone_display()는 choices의 한글 라벨을 가져옴
        return f"[{self.get_tone_display()}] {self.text[:20]}"


class LuckyOption(models.Model):
    TYPE_COLOR = "color"
    TYPE_ITEM = "item"
    TYPE_KEYWORD = "keyword"

    TYPE_CHOICES = [
        (TYPE_COLOR, "행운 컬러"),
        (TYPE_ITEM, "행운 아이템"),
        (TYPE_KEYWORD, "행운 키워드"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="종류")
    value = models.CharField(max_length=50, verbose_name="값")  # 예: "#2E8B57" or "beige" or "notebook"
    label = models.CharField(max_length=50, blank=True, verbose_name="표시 이름")  # 예: "네이비"
    is_active = models.BooleanField(default=True, verbose_name="사용 여부")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        verbose_name = "행운 컬러/아이템/키워드"
        verbose_name_plural = "행운 컬러/아이템/키워드"

    def __str__(self):
        return f"[{self.get_type_display()}] {self.label or self.value}"
