import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext
from app.db.models import Account, DatasetSnapshot, Document, DocumentChunk, Order, Ticket


class SupportRepository:
    def __init__(self, db: AsyncSession, auth: AuthContext):
        self.db = db
        self.auth = auth

    async def active_snapshot(self) -> DatasetSnapshot:
        result = await self.db.execute(
            select(DatasetSnapshot).where(DatasetSnapshot.is_active.is_(True)).limit(1)
        )
        snapshot = result.scalar_one_or_none()
        if snapshot is None:
            raise RuntimeError("No active dataset snapshot")
        return snapshot

    def account_access_clause(self):
        if self.auth.is_internal:
            return True
        if not self.auth.permitted_account_ids:
            return False
        return Account.id.in_(self.auth.permitted_account_ids)

    async def list_accounts(self) -> list[Account]:
        snapshot = await self.active_snapshot()
        statement = select(Account).where(Account.dataset_snapshot_id == snapshot.id)
        if not self.auth.is_internal:
            statement = statement.where(self.account_access_clause())
        result = await self.db.execute(statement.order_by(Account.name))
        return list(result.scalars().all())

    async def account_by_external_id(self, external_id: str) -> Account | None:
        snapshot = await self.active_snapshot()
        statement = select(Account).where(
            Account.external_id == external_id,
            Account.dataset_snapshot_id == snapshot.id,
        )
        if not self.auth.is_internal:
            statement = statement.where(self.account_access_clause())
        return (await self.db.execute(statement)).scalar_one_or_none()

    async def order_by_external_id(self, external_id: str) -> tuple[Order, Account] | None:
        snapshot = await self.active_snapshot()
        statement = (
            select(Order, Account)
            .join(Account, Account.id == Order.account_id)
            .where(
                Order.external_id == external_id,
                Order.dataset_snapshot_id == snapshot.id,
            )
        )
        if not self.auth.is_internal:
            statement = statement.where(self.account_access_clause())
        return (await self.db.execute(statement)).one_or_none()

    async def ticket_by_external_id(self, external_id: str) -> tuple[Ticket, Account] | None:
        snapshot = await self.active_snapshot()
        statement = (
            select(Ticket, Account)
            .join(Account, Account.id == Ticket.account_id)
            .where(
                Ticket.external_id == external_id,
                Ticket.dataset_snapshot_id == snapshot.id,
            )
        )
        if not self.auth.is_internal:
            statement = statement.where(self.account_access_clause())
        return (await self.db.execute(statement)).one_or_none()

    def document_access_clause(self):
        if self.auth.is_internal:
            return True
        if not self.auth.permitted_account_ids:
            return Document.account_id.is_(None)
        return or_(
            Document.account_id.is_(None),
            Document.account_id.in_(self.auth.permitted_account_ids),
        )

    async def document_chunk_by_id(
        self, document_id: uuid.UUID, chunk_id: uuid.UUID
    ) -> tuple[DocumentChunk, Document] | None:
        statement = (
            select(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(Document.id == document_id, DocumentChunk.id == chunk_id)
        )
        if not self.auth.is_internal:
            statement = statement.where(self.document_access_clause())
        return (await self.db.execute(statement)).one_or_none()

    async def customer_account_for_chat(self, account_id: uuid.UUID | None) -> Account | None:
        if account_id is None:
            return None
        statement = select(Account).where(Account.id == account_id)
        if not self.auth.is_internal:
            statement = statement.where(self.account_access_clause())
        return (await self.db.execute(statement)).scalar_one_or_none()

