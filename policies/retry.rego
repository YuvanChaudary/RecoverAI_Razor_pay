package recovery.retry

max_retries := 3

default retry_allowed := false
default retry_blocked := false

retry_allowed {
    input.retry_count < max_retries
}

retry_blocked {
    input.retry_count >= max_retries
}
