"""
immudb Cryptographic Immutable Audit Trail Service
Provides tamper-evident event logging, canonical JSON serialization, SHA-256 payload hashing,
and verification methods.
"""

import json
import logging
from typing import Dict, Any, Optional
from immudb import ImmudbClient
from backend.app.core.config import get_settings
from backend.app.schemas.audit import AuditEvent, AuditVerificationResult

logger = logging.getLogger("recoverai.immutable_audit_service")


class ImmutableAuditService:
    """
    Async-compatible immudb Cryptographic Audit Service.
    Enforces append-only semantics and SHA-256 tamper-evident verification.
    """

    KEY_PREFIX = "recoverai/audit"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        client: Optional[Any] = None
    ):
        settings = get_settings()
        self.host = host or settings.IMMUDB_HOST
        self.port = port or settings.IMMUDB_PORT
        self.database = database or settings.IMMUDB_DATABASE
        self.user = user or settings.IMMUDB_USER
        self.password = password or settings.IMMUDB_PASSWORD
        self._client = client
        self._local_audit_store: Dict[str, Dict[str, Any]] = {}

    def _get_client(self) -> ImmudbClient:
        if self._client is not None:
            return self._client
        client = ImmudbClient(f"{self.host}:{self.port}")
        client.login(self.user, self.password)

        if hasattr(client, "useDatabase"):
            client.useDatabase(self.database)
        elif hasattr(client, "databaseUse"):
            client.databaseUse(self.database)

        return client

    async def record_event(self, event: AuditEvent) -> Dict[str, Any]:
        """
        Records an audit event into immudb.
        Enforces canonical JSON serialization, SHA-256 payload hashing, and append-only deduplication.
        """
        # 1. Compute SHA-256 hash of canonical JSON
        computed_hash = event.compute_hash()
        event.payload_hash = computed_hash

        key = f"{self.KEY_PREFIX}/{event.event_id}"

        # 2. Check Append-Only Deduplication: Key must not be overwritten if already exists
        if key in self._local_audit_store:
            logger.info(f"Duplicate audit event key detected '{key}' -> Retaining original record (append-only)")
            return {
                "status": "DUPLICATE",
                "event_id": event.event_id,
                "key": key,
                "payload_hash": event.payload_hash,
                "persisted": True,
                "created": False,
                "details": "Existing audit event retained under append-only rules."
            }

        payload_dict = event.model_dump(mode="json")
        json_val = json.dumps(payload_dict, sort_keys=True)

        # 3. Persist to immudb
        try:
            client = self._get_client()
            if hasattr(client, "verifiedSet"):
                client.verifiedSet(key.encode("utf-8"), json_val.encode("utf-8"))
            elif hasattr(client, "set"):
                client.set(key.encode("utf-8"), json_val.encode("utf-8"))

            self._local_audit_store[key] = payload_dict
            logger.info(f"Immutable audit event recorded: key='{key}', hash='{computed_hash[:12]}...'")
            return {
                "status": "CREATED",
                "event_id": event.event_id,
                "key": key,
                "payload_hash": computed_hash,
                "persisted": True,
                "created": True
            }
        except Exception as e:
            logger.debug(f"immudb audit write unavailable for key '{key}': {str(e)}")
            return {
                "status": "ERROR",
                "event_id": event.event_id,
                "key": key,
                "payload_hash": computed_hash,
                "persisted": False,
                "created": False,
                "error": str(e)
            }

    async def verify_event(
        self,
        event_id: str,
        tampered_record: Optional[Dict[str, Any]] = None
    ) -> AuditVerificationResult:
        """
        Verifies cryptographic integrity of a recorded audit event.
        Retrieves record, reconstructs canonical payload, recalculates SHA-256,
        and compares with stored payload_hash.
        """
        key = f"{self.KEY_PREFIX}/{event_id}"
        record_dict = None

        if tampered_record is not None:
            record_dict = tampered_record
        elif key in self._local_audit_store:
            record_dict = self._local_audit_store[key]
        else:
            try:
                client = self._get_client()
                if hasattr(client, "verifiedGet"):
                    res = client.verifiedGet(key.encode("utf-8"))
                    record_dict = json.loads(res.value.decode("utf-8"))
                elif hasattr(client, "get"):
                    res = client.get(key.encode("utf-8"))
                    record_dict = json.loads(res.value.decode("utf-8"))
            except Exception as e:
                logger.error(f"Failed to fetch audit record '{key}' from immudb: {str(e)}")
                raise ValueError(f"Audit event '{event_id}' not found or unreadable: {str(e)}")

        if not record_dict:
            raise ValueError(f"Audit event '{event_id}' not found.")

        stored_hash = record_dict.get("payload_hash", "")

        try:
            reconstructed_event = AuditEvent(**record_dict)
            calculated_hash = reconstructed_event.compute_hash()
        except Exception as err:
            return AuditVerificationResult(
                valid=False,
                event_id=event_id,
                stored_hash=stored_hash,
                calculated_hash="CALC_ERROR",
                details=f"Malformed audit payload: {str(err)}"
            )

        is_valid = (stored_hash == calculated_hash)
        details = "Integrity verified: Hash matches canonical payload." if is_valid else "TAMPER DETECTED: Hash mismatch!"

        return AuditVerificationResult(
            valid=is_valid,
            event_id=event_id,
            stored_hash=stored_hash,
            calculated_hash=calculated_hash,
            details=details
        )
