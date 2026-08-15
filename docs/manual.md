# Wizard Hov Wizarding Operations Console --- Operator Manual

**Applies to:** Console v12\
**Source of truth reviewed:** `console/tui.py`\
**Purpose:** Daily operation, triage, event investigation, and
interpretation of the current Console UI.

------------------------------------------------------------------------

## 1. Quick start: "I have an error. What do I do?"

1.  Start Console with `wizops` or `wizops  tui`.
2.  Press `3` for **Overview** and check:
    -   Event Health for WARN / ERROR / FATAL activity.
    -   Event Activity for bursts or sustained event volume.
    -   Top Services for the service generating most events.
    -   Severity Trend for changes in ERROR, WARN, and FATAL counts.
    -   System at a Glance for CPU, memory, VRAM, and filesystem
        pressure.
3.  Press `1` for **Dashboard**.
4.  Narrow the event list:
    -   `s` cycles services.
    -   `v` cycles severity.
    -   `t` cycles time range.
    -   `/` searches event text and metadata.
    -   `a` shows all severities.
    -   `c` resets filters to the default attention view.
5.  Use the arrow keys to highlight a representative event.
6.  Read the Event Details, Message, Raw Event, and Related context.
7.  Press `2` for **Events / Forensics** and inspect the same pattern.
8.  Read the forensic panel in this order:
    -   Event Identity / Classification
    -   Diagnosis Basis
    -   Recommended Next Action
    -   Possible Remedy, if present
    -   Confidence
    -   Occurrence
    -   Evidence Summary
9.  Verify the raw event and related records before changing
    configuration.
10. Make one controlled change, retry once, refresh with `r`, and verify
    whether the event pattern stops.

**Rule:** A Recommended Next Action is a diagnostic step. A Possible
Remedy is a corrective direction. Do not treat either as an automatic
command executor.

------------------------------------------------------------------------

## 2. What Console is

Wizarding Operations Console is a terminal operations and forensic viewer
backed by the Console events database.

The current application has three views with deliberately different
jobs:

-   **Dashboard:** "What is wrong now?"
-   **Events:** "What happened and why?"
-   **Overview:** "What is the stack doing over time?"

Console reads events through `EventStore`, applies service, severity,
time, and search filters, and displays up to 1,000 matching events in
reverse chronological order.

Console guidance is currently **rule-based and evidence-linked**. It
does not independently prove root cause. The source explicitly instructs
the operator to verify raw events and related records before applying a
configuration change.

------------------------------------------------------------------------

## 3. Starting and leaving Console

Start:

    wizops

Quit:

    q

The application opens in **Dashboard** view with:

-   Severity filter: `ATTENTION`
-   Time range: `24H`
-   Service filter: `ALL`
-   Search: none

`ATTENTION` means WARN, ERROR, and FATAL events.

------------------------------------------------------------------------

## 4. Keyboard reference

  Key          Action
  ------------ -----------------------------------------------
  `1`          Dashboard
  `2`          Events / forensic investigation
  `3`          Overview
  `q`          Quit
  `r`          Refresh events and telemetry
  `/`          Open search
  `c`          Clear/reset filters
  `s`          Cycle service filter
  `v`          Cycle severity filter
  `a`          Show all severities
  `t`          Cycle time range
  `Enter`      Inspector / selected-event action
  `Esc`        Cancel search when the search field has focus
  Arrow keys   Move through DataTable rows

Hidden aliases also exist:

-   `d` opens Dashboard.
-   `e` opens Events.

These aliases are not shown in the footer.

### Filter cycles

`v` cycles through:

    ATTENTION → ALL → TRACE → DEBUG → INFO → WARN → ERROR → FATAL → ATTENTION

`ATTENTION` is a special combined filter for:

    WARN + ERROR + FATAL

`t` cycles through:

    1H → 6H → 24H → 7D → ALL → 1H

`s` cycles:

    ALL → each distinct service alphabetically → ALL

### Reset behavior

`c` resets:

-   Service to ALL
-   Severity to ATTENTION
-   Search to none

It does **not** reset the selected time range.

### Search behavior

Press `/`, type a search term, then press `Enter`.

Search checks:

-   message
-   raw event
-   category
-   model
-   request ID

The search is a substring search.

Press `Esc` while the search box is focused to cancel the search input
without applying a new value.

------------------------------------------------------------------------

## 5. Dashboard view

Open with `1`.

### Purpose

Dashboard is the operations view. Use it to identify the current problem
area and select an event for detailed inspection.

### Metric cards

The Dashboard has:

-   ERRORS
-   WARNINGS
-   INFO
-   TOTAL EVENTS

The displayed counts are lifetime database counts, not limited to the
active 24-hour filter.

The ERRORS card combines ERROR and FATAL in its displayed number.

The cards are clickable:

-   ERRORS filters to `ERROR`
-   WARNINGS filters to `WARN`
-   INFO filters to `INFO`
-   TOTAL EVENTS removes the severity filter

Clicking a card also moves the application to Dashboard.

### Top Services

The Top Services strip shows the five services with the most events in
the last 24 hours.

The strip is clickable. Each click cycles the service filter through
those current top-five services.

This is useful for rapidly moving between the noisiest services without
repeatedly pressing `s`.

### Attention card

The attention card reports the active severity view and lifetime
severity totals. It also reports how many database events are hidden
relative to the currently displayed query result.

Remember that the event query is capped at 1,000 rows.

### Event table

Columns:

-   Time (Local)
-   Severity
-   Service
-   Message (summary)

Events are sorted newest first by timestamp and event ID.

The highlighted row drives the inspector automatically.

### Event Details

Shows available event identity fields:

-   ID
-   Time
-   Severity
-   Service
-   Source type and source
-   Category, if present
-   Model, if present
-   Request ID, if present

### Message (summary)

This is a normalized, human-readable message.

Console has special summary handling for several formats, including
structured level/message logs, GIN HTTP logs, and JSON messages. Long
summaries are shortened for the table, while the inspector can display a
much larger summary.

### Raw Event (exact)

This is the original event after ANSI escape sequences and carriage
returns are cleaned.

If the raw event is valid JSON, Console pretty-prints it.

Use this panel when the summary has removed context or when exact fields
matter.

### Related (context)

Console scores related events using:

-   Same request ID: +100
-   Same model: +40
-   Same category: +30
-   Same service: +10

It returns up to 12 related events, ordered first by relation score and
then by event-ID proximity.

A high score means the records share stronger metadata. It does **not**
prove that one event caused another.

### Enter in Dashboard

Pressing `Enter` refreshes the selected event detail and focuses the
detail pane.

------------------------------------------------------------------------

## 6. Events / forensic investigation view

Open with `2`.

### Purpose

Events is the forensic view. It uses the same filtered event stream but
replaces the Dashboard inspector with a rule-based investigation panel.

This is the main view for answering:

-   What class of failure is this?
-   What evidence supports that classification?
-   What should I verify next?
-   Is there a plausible remedy?
-   Has this pattern happened before?

### Forensic panel sections

#### Event Identity / Classification

Displays the diagnosis class and diagnosis rule ID.

Current rule classes are:

  Rule                              Classification
  --------------------------------- -------------------------------
  `auth_credential_failure.v1`      AUTH / CREDENTIAL FAILURE
  `gpu_memory_pressure.v1`          GPU MEMORY PRESSURE
  `process_termination.v1`          PROCESS TERMINATION
  `deprecated_configuration.v1`     DEPRECATED CONFIGURATION
  `timeout_deadline.v1`             TIMEOUT / DEADLINE
  `request_cancellation.v1`         CLIENT / REQUEST CANCELLATION
  `database_transaction_state.v1`   DATABASE TRANSACTION STATE
  `none`                            UNCLASSIFIED EVENT

#### Priority

The current rule engine uses:

-   HIGH
-   MEDIUM
-   LOW
-   REVIEW

Priority comes from the matched diagnosis rule. It is not a calculated
incident severity score.

#### Diagnosis Basis

Explains why the event matched the rule.

#### Recommended Next Action

The next verification or investigation step.

This should normally be performed **before** the Possible Remedy.

#### Possible Remedy

A proposed corrective direction appears only when a deterministic
diagnosis rule provides one.

If no rule provides a remedy, Console displays **NO VERIFIED REMEDY**
and tells you that it lacks enough deterministic evidence to recommend a
configuration change.

#### Confidence

The current implementation displays the same value used by the rule's
priority/risk field. Therefore, treat this as a coarse rule label rather
than a statistically calculated confidence percentage.

#### Occurrence

Console searches for events with:

-   the same service, and
-   the same first 80 characters of the message

It displays:

-   First seen
-   Last seen
-   Count

This is a simple pattern fingerprint. Similar failures with different
prefixes may be counted separately.

#### Evidence Summary

Displays:

-   Service
-   Severity
-   Category
-   Number of related events

### Current diagnosis rules

#### Authentication / credential failure

Matches a message containing `401` plus API-key, authentication, or
unauthorized language.

Recommended workflow:

1.  Verify the configured API key or secret source.
2.  Confirm the container or service received the intended value.
3.  Retry one request.
4.  Do not paste secrets into Console.
5.  Correct the credential source or injection path only after
    identifying which service received a missing or incorrect value.

#### GPU memory pressure

Matches `out of memory` or `cudaMalloc failed`.

Recommended workflow:

1.  Check current VRAM consumers.
2.  Inspect loaded models.
3.  Unload competing models or reduce GPU offload/context pressure.
4.  Correlate nearby Ollama/llama events.
5.  Retry and verify that allocation failures stop.

#### Process termination

Matches terminated processes associated with killed, core-dumped, or
aborted language.

Recommended workflow:

1.  Inspect related events immediately before the termination.
2.  Look for OOM or allocation failures.
3.  Check journal/coredump evidence.
4.  Remedy the upstream cause before repeatedly restarting the service.

#### Deprecated configuration

Matches `deprecated`.

Recommended workflow:

1.  Identify the replacement named by the service.
2.  Update the source configuration during a maintenance pass.
3.  Restart as appropriate.
4.  Verify that the warning disappears.

#### Timeout / deadline

Matches `timeout`, `timed out`, or `deadline exceeded`.

Recommended workflow:

1.  Inspect related events for resource pressure.
2.  Check the target dependency or service.
3.  Fix a slow or unavailable dependency first.
4.  Increase timeouts only when healthy operations legitimately need
    more time.

#### Client / request cancellation

Matches connection cancellation or aborted-operation language.

Recommended workflow:

1.  Treat isolated events as informational noise.
2.  If repeated, correlate with client disconnects, proxy behavior, and
    model latency.
3.  Change configuration only after the repeated cause is confirmed.

#### Database transaction state

Matches `transaction in progress`.

Recommended workflow:

1.  Review adjacent Vector DB events.
2.  Inspect caller lifecycle.
3.  Look for a repeated transaction cleanup or retry pattern.
4.  Correct transaction lifecycle only after the repeated pattern is
    confirmed.

#### Unclassified event

If no rule matches, Console does not invent a remedy.

Use Message, Raw Event, and Related context. Repeated confirmed patterns
are candidates for a future diagnosis rule.

------------------------------------------------------------------------

## 7. Overview view

Open with `3`.

### Purpose

Overview is the stack health, capacity, trend, and collection-coverage
view.

It is not intended to replace event forensics. It tells you where to
look.

### Storage & Capacity

Displays:

-   Console database size
-   Filesystem used/free/total

The filesystem bar uses a green-to-red visual gradient.

The panel border changes with filesystem usage:

-   Below 60%: green
-   60% to below 75%: lime/yellow
-   75% to below 90%: orange
-   90% and above: red

Use the percentage and exact capacity numbers as the authoritative
values.

### Event Health --- Last 24H

Displays separate activity strips for:

-   ERROR
-   WARN
-   FATAL
-   INFO

Each row shows:

-   24-hour event count for that severity
-   a resampled hourly activity strip
-   peak events per hour

The panel also displays:

-   Total events in the last 24 hours
-   Attention events and attention percentage
-   Lifetime event count
-   First database timestamp
-   Last database timestamp

Attention here means ERROR + WARN + FATAL.

### Event Activity --- Last 24H / 15-minute buckets

This chart uses 96 real 15-minute buckets.

Metrics:

-   **PEAK:** largest exact 15-minute bucket
-   **P95:** robust visual ceiling used for chart scaling
-   **AVG:** average events per hour across the 24-hour window
-   **CURRENT HOUR:** sum of the last four 15-minute buckets
-   **TOTAL:** total activity represented in the 24-hour bucket query

The chart uses a 95th-percentile visual ceiling. Extreme spikes may be
visually clipped so that low and medium activity remain visible.

**Important:** the exact peak is preserved in the PEAK metric even when
the chart height is visually clipped.

The chart axis is:

    24h ago → 18h → 12h → 6h → now

Use this graph to distinguish:

-   isolated spikes
-   burst clusters
-   sustained activity
-   recent quiet periods

Do not diagnose severity from this chart alone. It measures event
volume.

### Top Services --- Last 24H

Displays up to 10 services ranked by event count.

Each row shows:

-   rank
-   service name
-   relative bar
-   exact event count
-   percentage share of 24-hour events

The bar scale is relative to the busiest service.

The panel also shows:

-   total 24-hour events
-   number of distinct services

A dominant service is a triage clue, not proof that the service is
faulty. A healthy but verbose service can dominate event volume.

### Collection & Coverage

Displays:

-   number of active collector-state records
-   latest collector-state update
-   event coverage date range
-   collector state indicator

`ACTIVE` here reflects the presence of collector-state records and
current Console state data. Use the last state update timestamp when
deciding whether collection may be stale.

### Events in Database

Displays:

-   lifetime event count
-   oldest event
-   newest event
-   database size

This is useful for understanding retention and collection history.

### Latest Attention Event

Shows the latest WARN, ERROR, or FATAL event.

Press `Enter` while in Overview to:

1.  clear service, severity, and search filtering,
2.  switch to Dashboard,
3.  refresh events,
4.  attempt to move the table cursor to the latest attention event,
5.  display that event in the inspector.

This is the fastest Overview-to-event handoff.

### Severity Trend --- Last 24H / 30-minute buckets

Displays independent normalized lanes for:

-   ERROR
-   WARN
-   FATAL

Each lane uses its own 95th-percentile scale. This preserves the shape
of low-volume FATAL activity instead of flattening it under higher WARN
or ERROR counts.

Because the lanes are independently normalized, **do not compare line
height between severities as absolute volume**.

Use the numeric totals and change metrics for volume comparison.

The statistics compare the current 24 hours with the preceding 24-hour
period.

The arrow shows direction:

-   `↑` increase
-   `↓` decrease
-   `→` unchanged

If the previous period has zero events and the current period is
nonzero, the current implementation reports a 100% increase.

### System at a Glance

Displays live local host probes for:

-   CPU load
-   Memory
-   VRAM
-   Filesystem

It also displays:

-   hostname
-   running Docker container count
-   loaded Ollama model count
-   collector count

#### CPU

CPU percentage is estimated as:

    1-minute load average / CPU count × 100

This is a load-based indicator, not direct CPU utilization sampling.

#### Memory

Memory usage is calculated from `/proc/meminfo` using MemTotal and
MemAvailable.

#### VRAM

VRAM is read from `nvidia-smi`.

If the command is unavailable or the output cannot be parsed, VRAM is
shown as unavailable.

#### Containers

Container count comes from `docker ps -q`.

#### Models

Loaded model count comes from `ollama ps`. The implementation accounts
for the command's header line.

#### Probe timeout

External local probe commands have a 1.5-second timeout. A failed or
slow command may produce an unavailable or empty value rather than
blocking Console.

------------------------------------------------------------------------

## 8. Recommended operating workflow

### Daily health check

1.  Open Overview.
2.  Check filesystem percentage.
3.  Check Event Health attention percentage.
4.  Look for recent Event Activity bursts.
5.  Identify dominant Top Services.
6.  Check Severity Trend direction.
7.  Check CPU, memory, and VRAM.
8.  If something looks abnormal, continue to Dashboard.

### Active troubleshooting

1.  Open Dashboard.
2.  Set a useful time range with `t`.
3.  Filter the suspected service with `s`.
4.  Filter severity with `v`, or use ATTENTION.
5.  Use `/` for a known model, request ID, error phrase, or category.
6.  Highlight an event.
7.  Read Message and Raw Event.
8.  Read Related context.
9.  Open Events with `2`.
10. Follow the Recommended Next Action.
11. Verify evidence before using the Possible Remedy.
12. Make one controlled change.
13. Retry the failed operation once.
14. Press `r`.
15. Check whether the occurrence pattern or new event stream changed.

### Investigating a spike

1.  Overview: inspect Event Activity.
2.  Note PEAK, P95, CURRENT HOUR, and TOTAL.
3.  Check Event Health to determine which severities were active.
4.  Check Top Services.
5.  Use Dashboard service and severity filters.
6.  Select an event near the spike period.
7.  Review Related events.
8.  Move to Events for diagnosis.

### Investigating GPU/model failures

1.  Overview: check VRAM.
2.  Check Event Health for ERROR/FATAL activity.
3.  Check Top Services for Ollama or model-related services.
4.  Dashboard: filter the service.
5.  Look for `out of memory`, `cudaMalloc`, termination, or
    watchdog/deadline events.
6.  Events: inspect GPU MEMORY PRESSURE or PROCESS TERMINATION
    classifications.
7.  Correlate related records before restarting repeatedly.

### Investigating API authentication failures

1.  Dashboard: search for `401`, `API key`, `unauthorized`, or the
    affected service.
2.  Select a representative event.
3.  Verify the exact Raw Event.
4.  Inspect Related events for other services failing in the same
    period.
5.  Events: confirm AUTH / CREDENTIAL FAILURE classification.
6.  Verify the configured secret source and actual service/container
    injection.
7.  Do not paste credentials into Console.
8.  Retry one request after correcting the confirmed injection/source
    problem.
9.  Refresh and verify that the event pattern stops.

------------------------------------------------------------------------

## 9. Understanding the filters

The status bar always shows:

-   SERVICE
-   SEVERITY
-   TIME
-   SEARCH

The view bar shows:

-   current view
-   purpose of the view
-   number of events shown
-   database path

### Query limit

Console returns at most 1,000 matching events.

If you are investigating a noisy period, narrow the query with time,
service, severity, or search rather than assuming the first 1,000 rows
represent the complete period.

### ATTENTION versus ALL

Use ATTENTION for operational triage.

Use ALL when:

-   an INFO event may explain an ERROR,
-   you need startup sequence context,
-   you are following request lifecycle behavior,
-   the service logs important state changes below WARN.

------------------------------------------------------------------------

## 10. The popup shown in your screenshot

The small floating character-choice popup containing accented/special
characters and number choices is **not created by this Console source**.

The reviewed Console code defines Textual widgets, the DataTable,
panels, search input, Header, and Footer. It contains no
compose-character candidate popup.

It is therefore coming from the terminal, desktop input method, or
compose/dead-key handling outside Console.

Its purpose is to choose a character variant. The number under a
candidate normally selects that candidate. `Esc` commonly dismisses the
popup.

If it becomes disruptive, investigate the active desktop input method or
compose-key configuration rather than changing `tui.py`.

------------------------------------------------------------------------

## 11. Important current limitations

### Rule-based diagnosis

Diagnosis uses explicit string-pattern rules. It is not an autonomous
root-cause engine.

A rule can classify a familiar event pattern, but the operator still
needs to verify raw and related evidence.

### No incident grouping yet

Events are investigated individually.

Console does not yet group multiple related records into a single
incident with lifecycle state.

A future incident layer could group correlated events and support states
such as:

-   UNREVIEWED
-   INVESTIGATING
-   KNOWN
-   RESOLVED
-   IGNORED

### Related-event scoring is metadata-based

Request ID, model, category, and service are useful correlation signals,
but the score is not causality.

### Occurrence fingerprint is simple

Occurrence matching uses the same service and first 80 message
characters.

Variable prefixes, IDs, timestamps, or differently formatted instances
of the same root problem may split one pattern into multiple occurrence
groups.

### "Confidence" is coarse

The current Confidence display reuses the rule's HIGH/MEDIUM/LOW/REVIEW
value. It is not a probability.

### Dashboard metric counts are lifetime counts

The metric cards use whole-database severity totals. They are not
recalculated for the active service/time/search filters.

### Overview is fixed to 24-hour telemetry in several panels

Changing the global time-range filter changes the event query, but
several Overview telemetry queries explicitly use the last 24 hours.

### Local probes depend on local commands

Docker, Ollama, and NVIDIA information depend on their corresponding
local commands being available and responding within the probe timeout.

------------------------------------------------------------------------

## 12. Good operator habits

-   Start broad in Overview and narrow deliberately.
-   Prefer ATTENTION for first-pass triage.
-   Read exact Raw Event data before editing configuration.
-   Use Related context as evidence, not proof.
-   Do not repeatedly restart a failing service before checking
    preceding OOM, termination, or dependency events.
-   Do not increase timeouts before checking dependency health and
    resource pressure.
-   Do not paste API keys or secrets into Console.
-   Make one controlled change at a time.
-   Retry once and verify the event stream after a change.
-   Promote repeated, confirmed patterns into new diagnosis rules rather
    than adding speculative remedies.

------------------------------------------------------------------------

## 13. Suggested next development priorities

The current visual framework is mature enough for real use. Further work
should be driven by actual troubleshooting sessions.

The strongest functional priorities are:

1.  **Incident correlation and grouping** --- combine related event
    chains into one operational incident.
2.  **Incident lifecycle state** --- UNREVIEWED, INVESTIGATING, KNOWN,
    RESOLVED, IGNORED.
3.  **Evidence-backed incident timeline** --- show the ordered sequence
    that led to the diagnosis.
4.  **Filter-aware dashboard metrics** --- optionally make metric cards
    reflect the active query.
5.  **Improved occurrence fingerprints** --- normalize variable IDs,
    timestamps, and request-specific text.
6.  **Explicit confidence model** --- separate operational priority from
    diagnosis confidence.
7.  **Operator notes / known-issue annotations** --- record what was
    verified and what fixed a recurring pattern.

Do not add all of these at once. Use Console during real failures and
record where the workflow creates friction. That evidence should
determine the next feature.

------------------------------------------------------------------------

## 14. One-page memory aid

**See trouble:** `3` Overview\
**Find source:** `1` Dashboard\
**Investigate cause:** `2` Events\
**Service:** `s`\
**Severity:** `v`\
**Time:** `t`\
**Search:** `/`\
**All severities:** `a`\
**Reset filters:** `c`\
**Refresh:** `r`\
**Inspect / Overview latest attention event:** `Enter`\
**Quit:** `q`

**Investigation order:**

    Overview signal
        ↓
    Dashboard event
        ↓
    Message + Raw Event
        ↓
    Related context
        ↓
    Events diagnosis
        ↓
    Recommended Next Action
        ↓
    Verify evidence
        ↓
    One controlled change
        ↓
    Retry once
        ↓
    Refresh and verify

------------------------------------------------------------------------

*Manual generated from the reviewed Console v12 `tui.py` implementation.
Update this document whenever bindings, diagnosis rules, query
semantics, or Overview metrics change.*
