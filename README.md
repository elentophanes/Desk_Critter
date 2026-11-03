# Desk_Critter

A little critter that sits on your taskbar (Windows) or above the Dock (macOS) and tells you, at a glance,
when something has **finished** (green eyes and a wave), **needs you** (it bounces and makes its noise),
or is **still working** (three bouncing dots).

It was built for the Claude apps (Claude Code and Claude Desktop), and works just as well for anything
that takes a while: OpenSCAD renders, slicing, Arduino / ESP32 compiles and uploads, test runs, backups,
your own scripts. Pick your critter: **Spider**, **Robot**, **Cat**, **Owl** or **ESP32 board**.

Python standard library only: nothing to install except Python itself.

The code and the documentation was created using AI native coding techniques with the assistance of 
Claude Code. Its part of my project to explore AI coding and generally get back into coding.

Feedback and contributions appreciated. 

In its current incarnation (v3.x) only the Windows version is tested, and the MacOS version is untested,
although the Mac version has been tested in v2.x.

> Desk_Critter is an independent project. It works with the Claude apps but is not affiliated with or
> endorsed by Anthropic. Claude is a trademark of Anthropic.

## What it does

- Sits just above the taskbar clock, on top of other windows, with a transparent background
- Blinks, bobs gently and waves; waves faster when you hover over it
- **Double-click** opens the Claude desktop app (falls back to claude.ai only if the app isn't found)
- **Drag** to move it; it remembers where you put it, also after a restart
  (handy for keeping it clear of the Windows notification pop-up, which covers the corner above the clock)
- **Right-click** for a menu: Open Claude / **Critter ▸** / **Test ▸** (Alert, Done, Working) / **Mute sounds** /
  Clear alert / Back to corner / **About Desk Critter…** / **Check for updates…** / Quit. **Back to corner** also forgets the remembered position.
  **About** shows the version (and the installed tag), the critter, Python / Tk, the folder it runs from,
  the copyright and the licence: handy when reporting a bug.
  **Mute sounds** (a tick in the menu, remembered) keeps the bounce and the wave but silences every sound.
  **Check for updates…** asks GitHub for the newest version tag and offers to open the project page if there
  is a newer one. It only goes online when you click it, and sends nothing but the request itself.
- **Choose your critter** from the right-click **Critter** menu. It switches straight away and is remembered.
- **Attention alert:** when something needs you, the critter bounces, waves fast, switches to its alert colours
  and plays its own alert sound (meow, "whoo … whooo", beep-boop, buzzer or boing).
- **Done (green eyes):** when something has finished and doesn't need you, the critter's eyes turn green
  (the robot and ESP32 board light up green too), it gives a happy wave and plays a quiet "done" sound.
  No bounce, no colour change.
- **Working dots:** three bouncing blue dots above the critter while a command or a Claude Code session is busy.
- Alert and green eyes clear when you switch to Claude, hover over the critter, or click it.

How the critter finds out (more in the sections below):

| Signal | Alert | Done | Working dots |
|---|---|---|---|
| Any command: `py tools\critter_run.py <command>` | if it fails | if it succeeds | yes |
| Your own scripts: `py tools\critter_event.py help` / `done` | yes | yes | – |
| Claude Code hooks | yes | yes | yes |
| Claude Desktop tool in normal chats (`tools/critter_mcp.py`) | yes | yes | – |
| Claude's Windows / macOS notifications | yes | yes, if Claude sends one (chats usually don't) | – |

## The critters

| Critter | Waves | Done (green eyes) | Alert |
|---|---|---|---|
| Spider | two front legs | green eyes, three soft taps | red-orange, yellow spots, cartoon **boing** (or a skitter of tiny feet) |
| Robot | right arm | green eyes, face screen tints green, antenna and chest lights pulse green (blue when idle), happy "bee-doo!" | red-orange, antenna light turns yellow, **beep-boop** warble |
| Cat | right paw, swishes tail | green eyes, a short **purr** | red-orange, tail swishes fast, **meows** |
| Owl | flaps both wings | green eyes, one soft "whoo" | red-orange, **"whoo ... whooo"** |
| ESP32 board | two jumper-wire arms | LED eyes pulse green with a glow, antenna trace and header pins turn green, two-tone "OK" chirp | board turns red-orange, LEDs red, piezo **bip-bip-biiip** |

Sounds: each critter plays its own alert sound instead of the Windows chime, and a quieter sound when
something has finished. Don't want the "done" sounds? Set `CRITTER_DONE_SOUNDS = False` near the top of
`desk_critter.pyw`. To change or replace a sound, see [Changing the sounds](#changing-the-sounds).

Run `py tools\preview_critters.py` to draw them all into `critters_preview.svg` (open it in a browser).

## Install

### 1. Prerequisites

- **Windows 10 or 11**
- **Python 3** from [python.org](https://www.python.org/downloads/). During setup, tick **"Add python.exe to PATH"**.
  Tkinter (used for drawing) is included by default. Check in PowerShell:
  ```powershell
  py --version
  ```
- **Claude desktop app**, with Windows notifications for Claude switched on
  (Settings → System → Notifications → Claude). The alert relies on these notifications.

No other packages are needed; the critter uses only the Python standard library.

### 2. Get the code

**Option A, with git** (recommended, makes updating easy):
```powershell
cd "$HOME\Documents"            # or wherever you keep your projects
git clone https://github.com/elentophanes/Desk_Critter.git
cd Desk_Critter
```

**Option B, without git:** on the repository page click **Code → Download ZIP**,
then extract it to a folder of your choice.

### 3. Run it

```powershell
pyw .\desk_critter.pyw
```

Or double-click `desk_critter.pyw` in File Explorer. `pyw` runs it without a console window.
The critter appears just above the clock.

Start with a particular critter, or list them:
```powershell
pyw .\desk_critter.pyw --critter robot      # spider, robot, cat, owl, esp32
py  .\desk_critter.pyw --list
```

Check that it works: right-click the critter → **Test ▸ Alert**. It should bounce, change colour and play its alert sound.

To stop it: right-click → **Quit**.

### 4. Install it outside the repo and start it with Windows (recommended)

Running the critter straight from the repo folder means it changes whenever the repo does.
`tools\install.py` copies a tagged version to its own folder instead:

```powershell
py tools\install.py --startup
```

This installs the newest version tag into `%USERPROFILE%\Tools\Desk_Critter` and creates a
**Desk Critter** shortcut in your Startup folder, so it starts each time you sign in.
Add a tag to pick a version (`py tools\install.py v2.1`) or `--dest D:\Somewhere` for another folder.

To update later: quit the critter, run `py tools\install.py`, start the critter again. Program files are
overwritten; your settings and log in that folder are kept, and nothing is deleted.
To stop it starting with Windows, remove the shortcut from the Startup folder (`Win+R`, `shell:startup`).

### 4b. Start it with Windows by hand (alternative)

1. Press `Win+R`, type `shell:startup`, press Enter. A folder opens.
2. In another File Explorer window, right-click `desk_critter.pyw` → **Show more options → Create shortcut**.
3. Move the new shortcut into the Startup folder.

The critter now starts each time you sign in. To stop that, remove the shortcut from the Startup folder.

## Trigger while Claude is in front (Claude Code hooks)

Windows notifications from Claude only appear when Claude is **not** the window in front, so on
notifications alone the critter stays quiet while you are looking at Claude. Claude Code can instead
tell the critter directly, through "hooks": small commands it runs when it finishes a turn (**Stop**)
and when it needs you (**Notification**). This works whatever window is in front. It covers
Claude Code sessions (including the Code tab of the desktop app), not ordinary chats.

Add this to `%USERPROFILE%\.claude\settings.json` (merge it with what is already there; adjust the
path if the critter is installed somewhere else):

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "pythonw \"C:/Users/<you>/Tools/Desk_Critter/critter_hook.py\" busy" } ] }
  ],
  "PostToolUse": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "pythonw \"C:/Users/<you>/Tools/Desk_Critter/critter_hook.py\" tick" } ] }
  ],
  "Notification": [
    { "hooks": [ { "type": "command",
                   "command": "pythonw \"C:/Users/<you>/Tools/Desk_Critter/critter_hook.py\" help" } ] }
  ],
  "Stop": [
    { "hooks": [ { "type": "command",
                   "command": "pythonw \"C:/Users/<you>/Tools/Desk_Critter/critter_hook.py\" done" } ] }
  ],
  "SessionEnd": [
    { "hooks": [ { "type": "command",
                   "command": "pythonw \"C:/Users/<you>/Tools/Desk_Critter/critter_hook.py\" end" } ] }
  ]
}
```

On a Mac the file is `~/.claude/settings.json` and each command is
`python3 "/full/path/to/critter_hook.py" <kind>`; see step 6 of [MAC_TESTING.md](MAC_TESTING.md).

**Working dots:** the first, second and last entries are what show the three bouncing
blue dots above the critter while a Claude Code session is busy. A prompt starts it (`busy`), each
finished tool call keeps it alive (`tick`), and it ends when the turn finishes, Claude needs you, or
the session closes. If a session dies without saying so, the dots stop after `WORKING_TIMEOUT`
(10 minutes without any event). Several sessions are tracked separately; the dots show while any of
them is working. `"async": true` makes those two hooks run in the background so they never slow
Claude down. Leave these three entries out if you only want "finished" and "needs you".

How it works: `critter_hook.py` appends one line to `%USERPROFILE%\.desk-critter\events.log`;
the critter watches that file (`WATCH_EVENTS`). The log shows `event (help|done|busy|end): ...`.
The hook prints nothing and always succeeds, so it cannot hold Claude up.

When an alert or green eyes start while Claude is already in front, the critter keeps them up for
`FRONT_HOLD_SECONDS` (10 s) before clearing; hover or click clears at once. When Claude is not in
front, it behaves as before: it stays until you switch to Claude.

To remove it, delete the entries from `settings.json`.

## Wave or alert on demand (your own scripts)

`tools/critter_event.py` tells the running critter directly. Put it at the end of a script, a batch file,
a scheduled task, or anything else that can run a command:

```
py tools\critter_event.py done                 green eyes and a happy wave
py tools\critter_event.py help                 alert: bounce, alert colours, sound
py tools\critter_event.py done "Report ready"  with your own text (it appears in desk_critter.log)
```
On a Mac use `python3 tools/critter_event.py done`. It works from the repo or from the installed copy
(`%USERPROFILE%\Tools\Desk_Critter\tools\critter_event.py`); the critter must be running.

It appends one line to `%USERPROFILE%\.desk-critter\events.log`, the same file the Claude Code hooks use;
the critter reacts within half a second and logs `event (done): <text>`.
To run a command *and* see the working dots while it runs, use `critter_run.py` (next section).

## Any long command: renders, compiles, uploads (`critter_run.py`)

Put `py tools\critter_run.py` in front of any command. The critter shows its blue working dots while the command
runs, then green eyes and a wave if it succeeded, or the alert if it failed:

```powershell
py tools\critter_run.py openscad -o part.stl part.scad
py tools\critter_run.py --name "ESP32 upload" arduino-cli upload -p COM5 --fqbn esp32:esp32:esp32 sketch
```

| The command… | The critter | Its log says |
|---|---|---|
| succeeds (exit code 0) | green eyes, wave, quiet done sound | `openscad finished (2 min 13 s)` |
| fails (any other exit code) | alert | `openscad failed (exit 1, 4 s)` |
| can't be found | alert | `openscad: command not found (openscad)` |
| is stopped with Ctrl+C | dots stop, no alert | `openscad interrupted` |

- The command's output appears as usual, and `critter_run` returns the command's exit code, so it works in scripts.
- `--name "text"` names the job (default: the program's name). Use `--` before a command that itself starts with `--`.
- Long jobs are fine: it tells the critter "still working" every minute.
- It runs programs, not PowerShell commands. For those, wrap them: `py tools\critter_run.py pwsh -c "Copy-Item ..."`.
- From the installed copy: `py C:\Users\<you>\Tools\Desk_Critter\tools\critter_run.py ...`. On a Mac use `python3 tools/critter_run.py ...`.

## Let Claude wave after every chat reply (Claude Desktop tool)

`tools/critter_mcp.py` gives Claude Desktop two small tools, **wave** and **alert**, which do exactly what
`critter_event.py done` / `help` do and nothing else. With one line in your preferences, Claude calls
`wave` at the end of every reply, or `alert` when it needs you. (It is an *MCP server*: the plug-in format
Claude Desktop uses for tools. It runs in the background; no window.)

**1. Check it works on its own** (with the critter running):
```
py C:\Users\<you>\Tools\Desk_Critter\tools\critter_mcp.py --selftest
```
It prints three answers and the critter waves.

**2. Tell Claude Desktop about it.** In Claude Desktop: **Settings → Developer → Edit Config**. This opens
the folder with `claude_desktop_config.json`; open that file in Notepad. If it is empty or has no `"mcpServers"`, make it:
```json
{
  "mcpServers": {
    "desk-critter": {
      "command": "py",
      "args": ["C:\\Users\\<you>\\Tools\\Desk_Critter\\tools\\critter_mcp.py"]
    }
  }
}
```
If it already has `"mcpServers": { ... }`, add just the `"desk-critter": { ... }` entry inside it, with a comma
between it and the entry before it. In JSON every `\` in a path is written `\\`. Keep any other settings in the file as they are.

**3. Restart Claude Desktop** completely: right-click its icon in the taskbar tray → Quit, then start it again.
In **Settings → Developer** "desk-critter" should show as *running*.

**4. Tell Claude to use it, in every chat.** In **Settings → Profile**, add to your personal preferences:
> Desktop critter: as the very last step of every reply, call the desk-critter `wave` tool. If you need my
> input, a decision or an approval before you can continue, call `alert` instead. Don't mention these calls.

The first time Claude calls it, Claude Desktop asks for permission: choose **Always allow**. That is safe
here: the tools can only make the critter wave or alert.

Notes: Claude follows this instruction nearly always, but it is an instruction, not a hard hook like Claude Code's.
The wave comes as Claude's last step, so it can appear a moment before the reply has finished showing.
If Settings → Developer shows an error, try the full path to Python instead of `py`
(find it with `py -c "import sys; print(sys.executable)"`).

## macOS

The Mac version was tested on a real Mac up to v2.4. Version 3.1 has not been retested on a Mac yet, so treat it as untested there, and please report anything that doesn't work.

### Prerequisites

- **Python 3.13** (or earlier) from [python.org](https://www.python.org/downloads/macos/). **Important:** do **not** use Python 3.14+, which bundles Tk 9.0; Tk 9.0 fails to make the window transparent. Python 3.13 and earlier bundle Tk 8.6, which works correctly.
  
  Verify after install (quit and reopen Terminal):
  ```bash
  python3.13 --version
  ```
  
  Check which Tk you have:
  ```bash
  python3.13 -c "import tkinter; r=tkinter.Tk(); print(r.tk.call('info','patchlevel'))"
  ```
  You want `8.6.x`, not `9.x.x`.

- **Claude desktop app**, with notifications allowed (System Settings → Notifications → Claude).

### Get the code

With git (recommended, makes updating easy):
```bash
cd ~/Documents
git clone https://github.com/elentophanes/Desk_Critter.git
cd Desk_Critter
```
Or download [the ZIP](https://github.com/elentophanes/Desk_Critter/archive/refs/heads/main.zip),
unpack it, and `cd ~/Downloads/Desk_Critter-main`. GitHub Desktop works too.

### Run it

```bash
python3.13 desk_critter.pyw
```

The spider appears bottom-right, above the Dock. Right-click (or Control-click) for the menu.

Try **Test ▸ Alert** (bounces, turns red-orange, plays a sound) and **Test ▸ Done** (eyes turn green).
Stop it with **Quit** in the menu, or Ctrl+C in Terminal.

Choose a different critter from the right-click **Critter** menu; it's remembered.

### Full Disk Access (for notifications)

The critter watches macOS' notification store. macOS requires permission:

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Click the **+** button and add **Terminal** (or whichever app you use to run the critter).
3. Quit that app completely and reopen it.
4. Run the critter again.

This is a one-time setup; it persists across restarts.

### Claude Code hooks (like Windows)

To make the critter react while Claude Code is running, even when Claude is in front, add this to `~/.claude/settings.json`:

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "python3.13 \"/full/path/to/critter_hook.py\" busy" } ] }
  ],
  "PostToolUse": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "python3.13 \"/full/path/to/critter_hook.py\" tick" } ] }
  ],
  "Notification": [
    { "hooks": [ { "type": "command",
                   "command": "python3.13 \"/full/path/to/critter_hook.py\" help" } ] }
  ],
  "Stop": [
    { "hooks": [ { "type": "command",
                   "command": "python3.13 \"/full/path/to/critter_hook.py\" done" } ] }
  ],
  "SessionEnd": [
    { "hooks": [ { "type": "command",
                   "command": "python3.13 \"/full/path/to/critter_hook.py\" end" } ] }
  ]
}
```

Replace `/full/path/to` with the actual folder (get it with `pwd` in Terminal).

This shows three bouncing blue dots above the critter while a Claude Code session is working, and green eyes when finished.

### Differences from Windows

- No taskbar-flash backup; notifications are the only trigger.
- The Dock height is a guess, so drag the critter where you want it; it remembers the position after a restart.
- A critter left on a second display returns to the corner after a restart.
- Python shows its own icon in the Dock while the critter runs.
- Use `python3.13` instead of `py` or `python3` to avoid Tk 9.0 issues.

## Updating

Your everyday critter is the **installed copy** (step 4 above), so `git pull` alone does not change it.

1. Get the latest code and tags:
   ```powershell
   cd "$HOME\Documents\Desk_Critter"     # your repo folder
   git checkout main
   git pull
   ```
2. Quit the critter (right-click → **Quit**), install the newest tag, start it again:
   ```powershell
   py tools\install.py
   Start-Process "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Desk Critter.lnk"
   ```
   `install.py` with no tag installs the newest version tag. Settings and log are kept; nothing is deleted.
3. If the new version changed `tools/critter_mcp.py`, restart Claude Desktop too (tray icon → Quit, start it again),
   because it keeps the old copy of the wave/alert tool running.

If you run the critter straight from the repo instead, `git pull` and a restart of the critter is enough.

## Going back to a baseline version

Each stable version is a git tag (see **Versions** below). To put an older version in your everyday
installed copy, quit the critter and install that tag, then start it again:

```powershell
py tools\install.py v2.7     # install version 2.7
py tools\install.py          # later: back to the newest version
```

Files that only exist in newer versions stay in the folder (the installer never deletes anything), which is harmless.
Desk_Critter's tags start at v3.0; the versions before it were developed privately (see **Versions**).

## Adding your own critter

1. Copy a file in `critters/`, e.g. `critters\robot.py` → `critters\frog.py`.
2. Change `NAME`, `ORDER`, the `COLOURS` (a `normal` and an `alert` set with the same keys) and the drawing in `draw()`.
3. Check it: `py tools\preview_critters.py preview.svg frog`, then open `preview.svg` in a browser.
4. Optional: give it its own sounds. Put short `.wav` files next to it and add
   `SOUND = "frog.wav"` (alert; without it the normal chime plays) and/or
   `SOUND_DONE = "frog_done.wav"` (Claude finished; without it, silent).
5. Restart the critter; **Frog** now appears in the right-click **Critter** menu.

Drawing rules, so every critter fits the same window: centre line x = 340, feet on y = 242, nothing above y = 94
(room to bounce) and keep within x = 226…454. Use the `eye()` helper so blinking and green eyes work automatically.
The full contract is at the top of `critters/__init__.py`. If a critter has an error, it is skipped
(or the spider takes over) and the problem is written to `desk_critter.log`.

## Changing the sounds

Each critter names its sound files in two lines at the top of `critters/<critter>.py`:
```python
SOUND = "owl.wav"            # alert (Claude needs you); without it the normal chime plays
SOUND_DONE = "owl_done.wav"  # Claude finished; without it, silent
```
The files live next to it in `critters/`. If a file is missing or can't play, the normal chime plays instead.

**Tweak a generated sound.** Every sound except the meow has a small function in `tools/make_sounds.py`
(the meow is `tools/make_meow.py`). Change its numbers, then rebuild just that one:
```
py tools\make_sounds.py owl          (Windows; on a Mac: python3 tools/make_sounds.py owl)
py tools\make_meow.py
```

**Use a recording instead.**
1. Save it as a **plain WAV** (16-bit PCM). Windows can only play plain WAV, not MP3 or compressed WAV;
   the same file then works on the Mac too. In Audacity: File → Export → Export as WAV → "Signed 16-bit PCM".
2. Keep it short (about 0.3–1.5 s) and trim the silence at the start, so it plays at once.
3. Give it its own name, e.g. `critters\owl_real.wav`, and point the critter at it: `SOUND = "owl_real.wav"`.
4. Restart the critter and use **Test ▸ Alert** / **Test ▸ Done** to hear it.

Your recordings are protected: the scripts only overwrite a `.wav` that is still exactly as they made it
(fingerprints in `tools/generated_sounds.json`). A file you replaced or edited is skipped with a message;
add `--force` to overwrite it anyway, e.g. `py tools\make_sounds.py owl --force`.

## Troubleshooting

| Problem | What to do |
|---|---|
| A pink/magenta box around the critter | Transparency only works on Windows. Make sure you run it with Windows Python, not WSL. |
| Double-click opens the browser instead of the app | The Claude app wasn't found. In PowerShell run `Get-StartApps \| ? Name -like "*Claude*"` and paste the AppID into `CLAUDE_APP_ID` near the top of `platforms/windows.py`. |
| The critter doesn't alert | Check that Windows notifications for Claude are switched on and Focus / Do not disturb is off. Then look at `desk_critter.log` next to the script: you should see `notification watcher started` and, when Claude wants you, `Claude notification (help): ...`. |
| No sound | Is **Mute sounds** ticked in the right-click menu? Check the volume and speakers. Critters play their own `.wav` files from `critters/` (see **Changing the sounds**); a critter without one falls back to the Windows "Notification" sound. To turn sounds off: `ALERT_SOUND = False` (alerts) or `CRITTER_DONE_SOUNDS = False` (done), near the top of `desk_critter.pyw`. |
| The Windows notification pop-up covers the critter | Drag the critter somewhere clear of the pop-up; it stays there. |
| A critter is missing from the menu | It has an error or misses `NAME`, `COLOURS` or `draw()`. See `desk_critter.log`. |
| The critter is the wrong size | Change `SCALE` near the top of `desk_critter.pyw` (e.g. `0.8` is bigger) and restart. |
| `desk_critter.log` keeps growing | Set `DEBUG_LOG = False` once everything works. |
| macOS: "DEPRECATION WARNING: The system version of Tk is deprecated", then it stops | You are on Apple's Python 3.9. Install Python 3 from python.org, quit and reopen Terminal. |
| macOS: `git clone` says password authentication is not supported | Download the ZIP in the browser or use GitHub Desktop; see **macOS → Get the code**. |
| `py` or `pyw` is not recognised | Python isn't on PATH. Re-run the Python installer and tick "Add python.exe to PATH". |

## How the alert works

- **Notifications (main trigger, v1.4):** polls Windows' notification store
  (`%LOCALAPPDATA%\Microsoft\Windows\Notifications\wpndatabase.db`, read-only) every 1.5 s
  for new entries from the Claude app (`Claude_*!Claude`).
- **Help or done (v1.6):** a notification containing one of `NEEDS_HELP_PHRASES`
  ("needs your input", "waiting for your input", "Allow Claude to ...") gives the full alert.
  Any other Claude notification (usually a short summary of what it finished) gives green eyes.
  If Claude starts using a new wording for "I need you", add it to `NEEDS_HELP_PHRASES`.
- **Taskbar flash (backup, v1.3):** a hidden shell-hook window listens for `HSHELL_FLASH` from `claude.exe`.
  Claude doesn't flash every time, which is why notifications became the main trigger.

Settings (size, speeds, sound, logging, default critter) are constants at the top of `desk_critter.pyw`.
Each critter's colours are at the top of its own file in `critters/`.
Your chosen critter and position are saved in `desk_critter_settings.json` (git-ignored).
With `DEBUG_LOG = True` events are written to `desk_critter.log` (git-ignored).

## Files

| File | Purpose |
|---|---|
| `desk_critter.pyw` | The program: window, alerts, menu, settings |
| `critters/` | One file per critter (`spider.py`, `robot.py`, `cat.py`, `owl.py`, `esp32.py`) plus shared drawing helpers (`_painter.py`) |
| `critter_hook.py` | Run by Claude Code hooks to tell the critter "finished" / "needs you" even when Claude is in front |
| `platforms/` | Operating-system specifics: `windows.py`, `macos.py`, `_base.py` (defaults and the list of functions each must provide) |
| `diag/notif_probe_mac.py` | macOS: read-only probe of the notification store, for debugging |
| `MAC_TESTING.md` | Step-by-step Mac test procedure and what to report back |
| `tools/make_sounds.py` | Synthesises all the other critter sounds into `critters/*.wav`; won't overwrite your recordings |
| `tools/generated_sounds.json` | Fingerprints of the generated sounds (how the scripts recognise a recording) |
| `tools/make_meow.py` | Synthesises the cat's meow into `critters/cat.wav` (tweak the numbers and re-run to change it) |
| `tools/preview_critters.py` | Draws all critters into an SVG for checking designs |
| `tools/critter_event.py` | Wave (`done`) or alert (`help`) on demand, from your own scripts |
| `tools/critter_run.py` | Runs any command: working dots while it runs, then green eyes or an alert |
| `tools/critter_mcp.py` | Claude Desktop tools `wave` / `alert` (tiny MCP server) so chats can signal the critter |
| `tools/install.py` | Installs a tagged version outside the repo, optionally with a start-with-Windows shortcut |
| `diag/attention_diag.pyw` | Diagnostic recorder used to find out how Claude signals attention |
| `diag/notif_probe.py` | Read-only probe of the Windows notification store |
| `diag/check.py` | Quick check: compiles every program file, lists critters, renders the preview |
| `LICENSE`, `COMMERCIAL.md` | PolyForm Noncommercial License 1.0.0; commercial licensing |
| `CONTRIBUTING.md`, `CLA.md` | How to contribute; the Contributor License Agreement |
| `CLAUDE.md` | Notes for Claude Code when it works on this project |

## Versions

| Tag | Change |
|---|---|
| v3.1 | Right-click → **About Desk Critter…** (version, installed tag, critter, Python / Tk, folder, copyright, licence), **Check for updates…**, **Mute sounds**; the tests are grouped in a **Test ▸** submenu |
| v3.0 | Published as **Desk_Critter**: renamed from an earlier private project, general-purpose events, PolyForm Noncommercial licence |
| v2.9 | `tools/critter_run.py`: run any command with working dots, then green eyes (success) or an alert (failure) |
| v2.8 | `tools/critter_mcp.py`: Claude Desktop tools so Claude waves after every chat reply |
| v2.7 | `tools/critter_event.py`: wave or alert on demand (normal Claude chats have no "finished" notification) |
| v2.6 | Every critter has its own alert sound and a quiet "done" sound (purr, hoo, bee-doo, chirp, taps) |
| v2.5 | Critters can have their own alert sound; the cat meows |
| v2.4 | "Working right now": bouncing dots while a Claude Code session is busy. **Now tested and confirmed working on macOS.** |
| v2.3 | Claude Code hooks: reacts even while Claude is in front; holds the signal 10 s in that case |
| v2.2 (not tagged separately; included in v2.3) | Windows / macOS code separated into `platforms/`; experimental macOS support |
| v2.1 | Robot and ESP32 board show "done" much more clearly (pulsing green lights, green screen / traces) |
| v2.0 | Several critters to choose from (spider, robot, cat, owl, ESP32 board); main program became one file for all critters |
| v1.6 | Green eyes when Claude has finished and doesn't need help |
| v1.5 | Remembers where you dragged it |
| v1.4 | Alerts on Claude's Windows notifications |
| v1.3 | Attention alert on taskbar flash (bounce, colour, chime) |

Versions before v3.0 were developed in a private repository and are listed for the record; their tags are
not in this repository. 1.0–1.2 (not committed): baseline, front legs wave in front of the body,
double-click opens the Claude desktop app.

## License

Desk_Critter is **source-available**, not open source in the OSI sense.

| Who | Terms |
|---|---|
| Individuals: personal, hobby, study and research use | ✅ Free under the [PolyForm Noncommercial License 1.0.0](LICENSE). You may use, modify and share it. |
| Schools, charities, non-profits, public bodies | ✅ Free under the same license |
| Companies and anyone using it for commercial purposes | 💼 Requires a [commercial license](COMMERCIAL.md) |

**Contributions are welcome!** Please read [CONTRIBUTING.md](CONTRIBUTING.md). A one-time
[Contributor License Agreement](CLA.md) is required before your first pull request is merged.

**Artwork and sounds:** the critter designs (drawn in code in `critters/*.py`) and their sounds
(`critters/*.wav`) are part of the software and covered by the same license.

**Trademark note:** Claude is a trademark of Anthropic. Desk_Critter works with the Claude apps but is an independent project,
not affiliated with or endorsed by Anthropic.

Copyright (c) 2026 Elentophanes
