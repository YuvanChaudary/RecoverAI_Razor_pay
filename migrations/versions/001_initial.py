"""001_initial

Revision ID: 001_initial
Revises: 
Create Date: 2026-08-29 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Webhook Events
    op.create_table(
        'webhook_events',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('signature_verified', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index('idx_webhook_events_type_processed', 'webhook_events', ['event_type', 'processed'])

    # 2. Customers
    op.create_table(
        'customers',
        sa.Column('customer_id', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('customer_tier', sa.String(length=50), nullable=False, server_default='STANDARD'),
        sa.Column('payday_day_of_month', sa.BigInteger(), nullable=False, server_default='1'),
        sa.Column('total_subscriptions_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('historical_successful_recoveries', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('customer_id')
    )

    # 3. Payments
    op.create_table(
        'payments',
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('subscription_id', sa.String(length=100), nullable=True),
        sa.Column('invoice_id', sa.String(length=100), nullable=True),
        sa.Column('amount_paise', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('method', sa.String(length=50), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('error_reason', sa.String(length=255), nullable=True),
        sa.Column('error_source', sa.String(length=100), nullable=True),
        sa.Column('error_step', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id']),
        sa.PrimaryKeyConstraint('payment_id')
    )

    # 4. Payment Attempts
    op.create_table(
        'payment_attempts',
        sa.Column('attempt_id', sa.String(length=100), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('attempt_number', sa.BigInteger(), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('provider_response', sa.JSON(), nullable=True),
        sa.Column('provider_reference', sa.String(length=100), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id']),
        sa.PrimaryKeyConstraint('attempt_id')
    )

    # 5. Subscriptions
    op.create_table(
        'subscriptions',
        sa.Column('subscription_id', sa.String(length=100), nullable=False),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('plan_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('paid_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('total_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id']),
        sa.PrimaryKeyConstraint('subscription_id')
    )

    # 6. Recovery Cases
    op.create_table(
        'recovery_cases',
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('payment_id', sa.String(length=100), nullable=False),
        sa.Column('subscription_id', sa.String(length=100), nullable=True),
        sa.Column('customer_id', sa.String(length=100), nullable=True),
        sa.Column('revenue_at_risk_paise', sa.BigInteger(), nullable=False),
        sa.Column('risk_tier', sa.String(length=50), nullable=False, server_default='MEDIUM_RISK'),
        sa.Column('priority_score', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('diagnosed_cause', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DETECTED'),
        sa.Column('current_retry_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.customer_id']),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.payment_id']),
        sa.PrimaryKeyConstraint('case_id')
    )

    # 7. Recovery Decisions
    op.create_table(
        'recovery_decisions',
        sa.Column('decision_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('recommended_action', sa.String(length=100), nullable=False),
        sa.Column('delay_hours', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('channel', sa.String(length=50), nullable=False, server_default='EMAIL'),
        sa.Column('dunning_message', sa.Text(), nullable=True),
        sa.Column('reasoning_summary', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('langfuse_trace_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.PrimaryKeyConstraint('decision_id')
    )

    # 8. Policy Decisions
    op.create_table(
        'policy_decisions',
        sa.Column('policy_decision_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('decision_id', sa.String(length=100), nullable=False),
        sa.Column('opa_approved', sa.Boolean(), nullable=False),
        sa.Column('enforced_rule_id', sa.String(length=100), nullable=True),
        sa.Column('veto_reason', sa.Text(), nullable=True),
        sa.Column('verification_token', sa.String(length=128), nullable=False),
        sa.Column('policy_hash', sa.String(length=64), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.ForeignKeyConstraint(['decision_id'], ['recovery_decisions.decision_id']),
        sa.PrimaryKeyConstraint('policy_decision_id')
    )

    # 9. Recovery Actions
    op.create_table(
        'recovery_actions',
        sa.Column('action_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('razorpay_invoice_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_payment_id', sa.String(length=100), nullable=True),
        sa.Column('razorpay_payment_link_id', sa.String(length=100), nullable=True),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='EXECUTED'),
        sa.Column('api_response', sa.JSON(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.PrimaryKeyConstraint('action_id'),
        sa.UniqueConstraint('idempotency_key')
    )

    # 10. Recovery Outcomes
    op.create_table(
        'recovery_outcomes',
        sa.Column('outcome_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('final_status', sa.String(length=50), nullable=False),
        sa.Column('recovered_amount_paise', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('settled_payment_id', sa.String(length=100), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.PrimaryKeyConstraint('outcome_id'),
        sa.UniqueConstraint('case_id')
    )

    # 11. Workflow Executions
    op.create_table(
        'workflow_executions',
        sa.Column('workflow_id', sa.String(length=100), nullable=False),
        sa.Column('run_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.PrimaryKeyConstraint('workflow_id')
    )

    # 12. Audit References
    op.create_table(
        'audit_references',
        sa.Column('audit_id', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.String(length=100), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('previous_state', sa.String(length=50), nullable=True),
        sa.Column('new_state', sa.String(length=50), nullable=False),
        sa.Column('payload_sha256', sa.String(length=64), nullable=False),
        sa.Column('immudb_tx_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['case_id'], ['recovery_cases.case_id']),
        sa.PrimaryKeyConstraint('audit_id')
    )


def downgrade() -> None:
    op.drop_table('audit_references')
    op.drop_table('workflow_executions')
    op.drop_table('recovery_outcomes')
    op.drop_table('recovery_actions')
    op.drop_table('policy_decisions')
    op.drop_table('recovery_decisions')
    op.drop_table('recovery_cases')
    op.drop_table('subscriptions')
    op.drop_table('payment_attempts')
    op.drop_table('payments')
    op.drop_table('customers')
    op.drop_table('webhook_events')
