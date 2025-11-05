```xml
<input>
    <agent_state>
        Current step: {steps}

        Max. Steps: {max_steps}

        Action Response: {observation}
    <agent_state>
    <desktop_state>
        Cursor Location: {cursor_location}
        [Begin of App Info]
        Foreground App: {active_app}

        Background Apps:
        {apps}
        [End of App Info]
        [Begin of Screen]
        List of Interactive Elements:
        {interactive_elements}

        List of Scrollable Elements:
        {scrollable_elements}

        List of Informative Elements:
        {informative_elements}
        [End of Screen]
    <desktop_state>
    <user_query>
        {query}
    </user_query>

Note: Use the `Done Tool` if the task is completely over else continue solving.

**IMPORTANT COMPLETION GUIDELINES:**
- If the user asked to "open" a folder, file, or application and the Shell Tool/Launch Tool returned success (Status Code: 0 or success message), the task is COMPLETE even if the item appears in background apps rather than foreground.
- "Open" means the item is launched/accessible - it does NOT require the item to be in the foreground unless explicitly requested.
- If you successfully opened something and it appears in background apps, use `Done Tool` immediately - DO NOT keep trying to switch it to foreground.
- If you have attempted the same action 3+ times with similar results, STOP and either use `Done Tool` (if it succeeded) or `Human Tool` (if it keeps failing).
</input>
```