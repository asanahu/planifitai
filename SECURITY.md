# PHI Encryption

Sensitive profile fields (`weight_kg`, `height_cm`, `medical_conditions`) are
encrypted at the application layer using Fernet (AES-GCM). The database stores
only ciphertext bytes.

## Configuration

Set the following environment variables:

- `PHI_ENCRYPTION_KEY`: Base64 url-safe 32 byte key. Generate with:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- `PHI_PROVIDER`: `app` (default) or `pgcrypto` (future option).

## Key Rotation

Use `scripts/rotate_phi_key.py` to re-encrypt existing PHI when rotating keys:

```bash
OLD_PHI_KEY=<old> NEW_PHI_KEY=<new> python scripts/rotate_phi_key.py
```

After rotation update `PHI_ENCRYPTION_KEY` and restart the app.

## Limitations

Encrypted values cannot be searched or filtered by range. Additional techniques
like hashing or tokenization are required for such queries.
