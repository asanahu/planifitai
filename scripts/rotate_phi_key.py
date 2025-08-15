import os

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.security.crypto import AppCryptoProvider


def rotate_phi_key(old_key: str, new_key: str, session: Session) -> None:
    """Re-encrypt all PHI fields from old_key to new_key."""
    old = AppCryptoProvider(old_key)
    new = AppCryptoProvider(new_key)
    rows = session.execute(
        text("SELECT id, weight_kg, height_cm, medical_conditions FROM user_profiles")
    ).mappings()
    for row in rows:
        w = old.decrypt_float(row["weight_kg"])
        h = old.decrypt_float(row["height_cm"])
        m = old.decrypt_str(row["medical_conditions"])
        session.execute(
            text(
                "UPDATE user_profiles SET weight_kg=:w, height_cm=:h, medical_conditions=:m WHERE id=:id"
            ),
            {
                "w": new.encrypt_float(w),
                "h": new.encrypt_float(h),
                "m": new.encrypt_str(m),
                "id": row["id"],
            },
        )
    session.commit()


def main() -> None:  # pragma: no cover - CLI usage
    old_key = os.environ["OLD_PHI_KEY"]
    new_key = os.environ["NEW_PHI_KEY"]
    with SessionLocal() as session:
        rotate_phi_key(old_key, new_key, session)


if __name__ == "__main__":  # pragma: no cover
    main()
