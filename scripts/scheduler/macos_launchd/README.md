# macOS launchd Setup

Use these later on a Mac. Edit paths first.

1. Copy plist files to:

```bash
~/Library/LaunchAgents/
```

2. Load:

```bash
launchctl load ~/Library/LaunchAgents/com.gloc.rloc.plist
launchctl load ~/Library/LaunchAgents/com.gloc.oloc.plist
```

3. Unload:

```bash
launchctl unload ~/Library/LaunchAgents/com.gloc.rloc.plist
launchctl unload ~/Library/LaunchAgents/com.gloc.oloc.plist
```

Notes:

- Replace `/path/to/New project 2` with the real project path on Mac.
- Replace `python` with the Mac Python path if needed.
- Vloc Executor remains OFF.
