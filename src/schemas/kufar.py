from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class KufarImage(BaseModel):
    path: str


class KufarAd(BaseModel):
    ad_id: int | str
    subject: str
    ad_link: str
    price_byn: int = Field(default=0)
    list_time: datetime
    images: list[KufarImage] = Field(default_factory=list)

    @property
    def parsed_price(self) -> float:
        return round(self.price_byn / 100, 2)

    @property
    def timestamp(self) -> int:
        return int(self.list_time.timestamp())

    @property
    def image_path(self) -> str | None:
        return self.images[0].path if self.images else None


class KufarRegionLabels(BaseModel):
    ru: str = ""

    @field_validator("ru", mode="before")
    @classmethod
    def clean_name(cls, v: str | None) -> str:
        if not v:
            return ""
        return str(v).lower().replace("ё", "е")


class KufarRegionItem(BaseModel):
    id: str
    pid: str | None = None
    type: str
    region: int | None = None
    area: int | None = None
    tag: str | None = None

    labels: KufarRegionLabels | None = None
    label: KufarRegionLabels | None = None

    @property
    def ru_name(self) -> str:
        if self.labels and self.labels.ru:
            return self.labels.ru
        if self.label and self.label.ru:
            return self.label.ru
        return ""
