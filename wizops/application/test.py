def severity(self) -> SeverityStatus:

    counts24 = self.store.severity_counts_last_24h()
    previous = self.store.previous_severity_counts()

    bucket_rows = self.store.severity_buckets_last_24h()

    chart = {
        "ERROR": [0] * 48,
        "WARN": [0] * 48,
        "FATAL": [0] * 48,
    }

    for bucket, severity, count in bucket_rows:
        if (
            bucket is not None
            and severity in chart
            and 0 <= int(bucket) < 48
        ):
            chart[severity][int(bucket)] = int(count)

    stats = []

    for severity in ("ERROR", "WARN", "FATAL"):

        current = counts24.get(severity, 0)
        previous_count = previous.get(severity, 0)

        delta = (
            (current - previous_count) / previous_count * 100
            if previous_count
            else (100.0 if current else 0.0)
        )

        arrow = (
            "↑"
            if delta > 0
            else "↓"
            if delta < 0
            else "→"
        )

        stats.append(
            f"{severity} {current:,} {arrow}{abs(delta):.0f}%"
        )

    return SeverityStatus(
        counts24=counts24,
        previous=previous,
        chart=chart,
        stats=stats,
        )
