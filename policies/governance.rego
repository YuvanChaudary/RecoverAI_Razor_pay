package recovery.governance

import data.recovery.retry

default allow := false

# Allow decision is true ONLY if there are zero rule violations
allow {
    count(violations) == 0
}

# RULE-001: Maximum Retry Limit
# If action is RETRY_SCHEDULED, retry_count must be < 3
violations[msg] {
    input.action == "RETRY_SCHEDULED"
    input.retry_count >= retry.max_retries
    msg := sprintf("RULE-001: Exceeded maximum retry limit (%d >= %d)", [input.retry_count, retry.max_retries])
}

# RULE-002: Minimum Cooldown
# If action is RETRY_SCHEDULED, cooldown_hours must be >= 24
violations[msg] {
    input.action == "RETRY_SCHEDULED"
    input.cooldown_hours < 24
    msg := sprintf("RULE-002: Insufficient cooldown hours (%.2f < 24)", [input.cooldown_hours])
}

# RULE-003: Terminal Decline Protection
# If is_terminal_decline is true, action cannot be RETRY_SCHEDULED
violations[msg] {
    input.is_terminal_decline == true
    input.action == "RETRY_SCHEDULED"
    msg := "RULE-003: Retry action prohibited on terminal failure decline"
}

# RULE-004: AI Confidence Floor
# Confidence must be >= 0.80
violations[msg] {
    input.confidence < 0.80
    msg := sprintf("RULE-004: AI confidence below threshold (%.2f < 0.80)", [input.confidence])
}

# RULE-005: Pre-Debit Notice
# If pre_debit_notice_required is true, pre_debit_notice_sent must be true
violations[msg] {
    input.pre_debit_notice_required == true
    input.pre_debit_notice_sent != true
    msg := "RULE-005: Pre-debit notice required but not sent"
}
