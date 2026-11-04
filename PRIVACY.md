# What Desk Critter accesses

Everything Desk Critter reads, writes, watches, starts and connects to, so you can check it yourself.
This describes v3.2. All of it runs as your own user account: Desk Critter never needs administrator
rights, installs no service and doesn't touch the Windows registry.

**In short:** it sends nothing anywhere. It has no telemetry, analytics or crash reports. It only
connects to the internet when **you** choose **Check for updates…**, and it only opens a web page when you
say yes, or when you double-click the critter and the Claude app can't be found. It keeps a small local
log (see [The log file](#the-log-file)).

## Network

| When | What | Sends |
|---|---|---|
| You choose **Check for updates…** in the right-click menu | Reads the list of version tags from `https://api.github.com/repos/elentophanes/Desk_Critter/tags` | A normal web request with `User-Agent: Desk-Critter/<version>`. GitHub sees your IP address, as with any web page. It reads at most 1 MB of the answer and uses only the tag names: nothing is downloaded or run. |
| A newer version is found and you click **Yes** | Opens the project page on GitHub in your browser | Whatever your browser sends |
| You double-click the critter and the Claude app can't be found | Opens `https://claude.ai` in your browser | Whatever your browser sends |

Nothing else in the critter opens a network connection. `tools/install.py` only runs `git` on your
local repository; it doesn't fetch anything itself.

## What it watches

### Windows

| What | How | What is kept |
|---|---|---|
| **Taskbar flashes** | A hidden window registered for shell messages (`RegisterShellHookWindow`). Windows tells it whenever *any* program flashes its taskbar button. For each flash it reads the program name of that window. | Only if the program name contains `claude` does it read the window title, write name and title to the log, and react. For any other program it reads no title and logs only `taskbar flash (other program)`. |
| **Claude's notifications** | Reads Windows' notification database, read-only, every 1.5 s: `%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db`. The query selects only notifications from the Claude app (AppID `Claude_…!Claude`). | The notification text decides between "needs you" and "done", and is written to the log. Notifications from other apps are not read. |
| **Which program is in front** | The program name of the foreground window (`GetForegroundWindow`) | Compared with `claude`; not logged |
| **Screen size** | Work area and DPI, to place the critter above the clock | Not kept |

### macOS

| What | How | What is kept |
|---|---|---|
| **Claude's notifications** | Reads macOS' notification database, read-only, every 1.5 s (`~/Library/Group Containers/group.com.apple.usernoted/db2/db`, or the older location from `getconf DARWIN_USER_DIR`). The query selects only apps whose identifier contains `claude`. | As on Windows: the text decides "needs you" or "done", and is written to the log. |
| **Which app is in front** | `lsappinfo front` | Compared with `claude`; not logged |

macOS protects the notification database, so the program that runs Python (usually Terminal) needs
**Full Disk Access**. Be aware that this setting gives *that program* access to all your files, not only
to the database. If you'd rather not grant it, the critter still works with Claude Code hooks and the
tools; it just won't see Claude's notifications. macOS has no taskbar-flash watcher.

## Files

`<program folder>` is where `desk_critter.pyw` is: your repo folder, or `%USERPROFILE%\Tools\Desk_Critter`
when installed with `tools\install.py`.

| File | Access | Contents |
|---|---|---|
| `<program folder>\desk_critter_settings.json` | Read and write | Chosen critter, remembered position, mute on/off |
| `<program folder>\desk_critter.log`, `desk_critter.log.1` | Append | See [The log file](#the-log-file) |
| `<program folder>\INSTALLED_VERSION.txt` | Read | The installed tag, written by `tools\install.py` |
| `<program folder>\critters\` | Read | The critters' code and sounds |
| `~\.desk-critter\events.log` (`%USERPROFILE%\.desk-critter\events.log` on Windows) | The critter reads it; the hook and tools append to it. On macOS and Linux the `.desk-critter` folder is made readable by you only; on Windows it's inside your user profile, which other standard users can't read. | One line per event: time, kind (`help`, `done`, `busy`, `tick`, `end`), Claude Code session ID, and text of up to 300 characters, e.g. `MyProject \| Claude Code finished` or `MyProject \| used Bash`. Started afresh when it passes 64 KB. |
| The notification database (above) | Read only (opened with a read-only URI that stays read-only whatever characters the path contains) | Not changed |

No other files are read or written.

### The log file

`desk_critter.log` is on by default (`DEBUG_LOG = True` near the top of `desk_critter.pyw`). It stays on
your computer, is never sent anywhere, and is excluded from Git. It contains:

- start-up details: platform, chosen critter, settings changes
- the text of each Claude notification and each event (except the frequent tool-call `tick` events),
  which can include your Claude Code project folder name and Claude's message
- taskbar flashes on Windows: for Claude's windows the program name and window title; for any other
  program only the words `taskbar flash (other program)`
- update checks and their result

When it passes 256 KB (`LOG_MAX_BYTES`) it is renamed `desk_critter.log.1`, replacing the previous one, and a
new log starts, so the two together never grow beyond about half a megabyte. To turn it off, set
`DEBUG_LOG = False` and restart the critter; you can then delete both files.

## Programs it starts

| Program | When |
|---|---|
| `powershell -NoProfile -Command "Get-StartApps ..."` (Windows) | Once at start, hidden, to find how to open the Claude app: only the Start-menu entry named exactly `Claude` is used. Skipped if Claude is found in a usual install folder, or if you set `CLAUDE_APP_ID`. |
| The Claude app | When you double-click the critter (Windows: its program file or Start-menu entry; macOS: `open -a Claude`) |
| `afplay` (macOS) | To play the critter's sounds. Windows plays them itself (`winsound`). |
| `lsappinfo`, `getconf` (macOS) | See above |

## What changes on your computer, and only when you ask

| You run or set up | What it does |
|---|---|
| `py tools\install.py` | Copies the program files of a tag (signed by the maintainer, unless you add `--allow-unsigned`) into `%USERPROFILE%\Tools\Desk_Critter` (or `--dest`). Overwrites older program files there; never deletes anything. |
| `py tools\install.py --startup` | Also creates a **Desk Critter** shortcut in your Startup folder, so the critter starts each time you sign in. Remove it via `Win+R`, `shell:startup`. |
| Claude Code hooks (you add them to `~\.claude\settings.json`) | Claude Code runs `critter_hook.py` on each turn start, tool call, notification, turn end and session end. It receives Claude Code's event details on standard input and uses only the event name, the session ID, the project folder name (not the full path), the message and the tool name, to write one line to the events file. It prints nothing and always exits successfully, so it can't block Claude Code. |
| Claude Desktop tool (you add `tools/critter_mcp.py` to `claude_desktop_config.json`) | Claude Desktop runs it and talks to it over standard input and output only. Its two tools, `wave` and `alert`, write one line to the events file. |
| `py tools\critter_run.py <command>` | Runs the command **you** give it and writes start and end events. A `.bat`/`.cmd` file runs through `cmd.exe`; arguments containing characters `cmd.exe` would act on (`& \| < > ^ % ! "`) are refused. |
| `py tools\critter_event.py done` / `help` | Writes one line to the events file |

## The events file and other programs

Any program running under your account can write to `~\.desk-critter\events.log`. The worst it can do is
make the critter show false alerts, green eyes or working dots, and put text in the log. The critter only
accepts the five event kinds above. It never runs, opens or follows anything from an event's text.

## Check it yourself

All of the above can be checked in the source, which uses only the Python standard library
(`py diag\check.py` confirms that). These searches find every place that touches the network, files or
other programs:

```powershell
cd "$HOME\Documents\Desk_Critter"
Select-String -Path *.py,*.pyw,platforms\*.py,tools\*.py,critters\*.py -Pattern 'urlopen|webbrowser|socket|subprocess|startfile|open\(|sqlite3|winsound|user32|kernel32'
```

macOS / Linux: `grep -nE 'urlopen|webbrowser|socket|subprocess|open\(|sqlite3|afplay' *.py *.pyw platforms/*.py tools/*.py critters/*.py`

Found something that doesn't match this page? Please report it; see [SECURITY.md](SECURITY.md).
