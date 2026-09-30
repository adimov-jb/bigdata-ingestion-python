import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bronze_bucket: str
    aws_endpoint_url: str | None
    trino_host: str
    trino_port: int

    @classmethod
    def from_env(cls) -> "Settings":
        bronze_bucket = os.getenv("BRONZE_BUCKET")
        if not bronze_bucket:
            raise RuntimeError(
                "BRONZE_BUCKET não definido. Localmente ele vem de platform/local.env, "
                "gerado pelo terraform apply do repositório Terraform."
            )
        return cls(
            bronze_bucket=bronze_bucket,
            # Definido só no ambiente local (LocalStack); na AWS fica vazio.
            aws_endpoint_url=os.getenv("AWS_ENDPOINT_URL") or None,
            trino_host=os.getenv("TRINO_HOST", "trino"),
            trino_port=int(os.getenv("TRINO_PORT", "8080")),
        )
