"""family_subscription_lifecycle

Revision ID: e6c1a4b8d923
Revises: d5b9f3a7c612
Create Date: 2026-10-23 15:00:00.000000

Adds the columns the subscription lifecycle needs (cancel at period end, past due, provider references,
price snapshot) and the payment_events table used for webhook idempotency and audit. Existing subscriptions keep their
status and dates; none of the new columns changes what an existing row is entitled to.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'e6c1a4b8d923'
down_revision: Union[str, None] = 'd5b9f3a7c612'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = sqlmodel.sql.sqltypes.AutoString


def upgrade() -> None:
    with op.batch_alter_table('family_subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('cancelled_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('past_due_since', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('provider', S(), nullable=True))
        batch_op.add_column(sa.Column('provider_checkout_id', S(), nullable=True))
        batch_op.add_column(sa.Column('provider_subscription_id', S(), nullable=True))
        batch_op.add_column(sa.Column('last_payment_status', S(), nullable=True))
        batch_op.add_column(sa.Column('last_event_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('price_minor', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('currency', S(), nullable=True))
        batch_op.create_index('ix_family_subscriptions_provider_checkout_id', ['provider_checkout_id'], unique=False)
        batch_op.create_index('ix_family_subscriptions_provider_subscription_id', ['provider_subscription_id'], unique=False)

    op.create_table(
        'payment_events',
        sa.Column('id', S(), nullable=False),
        sa.Column('provider', S(), nullable=False),
        sa.Column('event_id', S(), nullable=False),
        sa.Column('event_type', S(), nullable=False),
        sa.Column('subscription_id', S(), nullable=True),
        sa.Column('outcome', S(), nullable=False),
        sa.Column('summary', sa.JSON(), nullable=True),
        sa.Column('received_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id'),
    )
    op.create_index('ix_payment_events_event_id', 'payment_events', ['event_id'])
    op.create_index('ix_payment_events_subscription_id', 'payment_events', ['subscription_id'])
    op.create_index('ix_payment_events_received_at', 'payment_events', ['received_at'])


def downgrade() -> None:
    op.drop_index('ix_payment_events_received_at', table_name='payment_events')
    op.drop_index('ix_payment_events_subscription_id', table_name='payment_events')
    op.drop_index('ix_payment_events_event_id', table_name='payment_events')
    op.drop_table('payment_events')
    with op.batch_alter_table('family_subscriptions', schema=None) as batch_op:
        batch_op.drop_index('ix_family_subscriptions_provider_subscription_id')
        batch_op.drop_index('ix_family_subscriptions_provider_checkout_id')
        for col in ('currency', 'price_minor', 'last_event_at', 'last_payment_status', 'provider_subscription_id',
                    'provider_checkout_id', 'provider', 'past_due_since', 'cancelled_at', 'cancel_at_period_end'):
            batch_op.drop_column(col)
