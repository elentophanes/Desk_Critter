# Testing Desk Critter on a Mac

The Mac version was written on Windows and first ran on a real Mac on 2026-10-09. The window, menu,
alert and notification watcher work there, **provided Python uses Tk 8.6** (step 1). Still to check:
whether "done" (green eyes) ever fires from Mac notifications, and position memory after a restart.
Do the steps in order and note what each one shows; the list of what to report is at the bottom.

Everything is typed into **Terminal** (press `Cmd+Space`, type `Terminal`, press Return).
Run each command on its own line.

## 1. Check Python

```bash
python3 --version
```

Shows the Python version. **If it shows 3.9, or the command is not found, install Python 3.13 from
<https://www.python.org/downloads/macos/>** (see below for why 3.13), then quit Terminal (`Cmd+Q`),
reopen it and check again.

Python 3.9 is the one that comes with Apple's developer tools. Its built-in Tk (used for drawing) is
too old: it prints "DEPRECATION WARNING: The system version of Tk is deprecated" and can then stop
Python dead. The python.org installer includes a working Tk.

**Important: get Tk 8.6, not Tk 9.0.** Starting with Python 3.14, the python.org macOS installer
switched from bundling Tcl/Tk 8.6 to Tcl/Tk 9.0. Tk 9.0 (confirmed at 9.0.4) silently fails to make
the window background see-through — the critter shows as a solid black box instead of floating
transparently, with no error anywhere. Check which one you have:

```bash
python3 -c "import tkinter; r=tkinter.Tk(); print(r.tk.call('info','patchlevel')); r.destroy()"
```

If that prints `9.x.x`, install Python **3.13** instead (pick a 3.13 release from the "Looking for a
specific release?" list on the downloads page, not the top "Download Python" button, which gives you
the latest). It installs alongside any existing newer Python rather than replacing it. Then run
everything below with `python3.13` instead of `python3`.

## 2. Get the code

### Option A: git in Terminal (easiest to update)

```bash
cd ~/Documents
git clone https://github.com/elentophanes/Desk_Critter.git
cd Desk_Critter
```

Downloads the code into a `Desk_Critter` folder and moves into it. Everything below is run from there.

### Option B: download a ZIP in the browser

Open <https://github.com/elentophanes/Desk_Critter/archive/refs/heads/main.zip>. A ZIP lands in your
Downloads folder (double-click it if it isn't unpacked), giving a `Desk_Critter-main` folder. Then:

```bash
cd ~/Downloads/Desk_Critter-main
```

### Option C: GitHub Desktop

**File → Clone repository** → `elentophanes/Desk_Critter`, then `cd` into that folder in Terminal.

## 3. Probe the notifications (read-only)

```bash
python3 diag/notif_probe_mac.py
```

This only reads; it changes nothing. It reports whether macOS' notification store can be opened,
which apps have notifications in it, and what Claude's notifications look like.

**If it says it could not open the database:**

1. Open **System Settings → Privacy & Security → Full Disk Access**.
2. Switch it on for **Terminal** (use the **+** button to add it if it isn't listed).
3. Quit Terminal completely (`Cmd+Q`) and open it again.
4. `cd` back into the code folder (step 2) and run the probe again.

macOS protects its notification store, and Full Disk Access is the only way a script can read it.

**If it says no Claude notifications are stored:** make sure notifications are allowed for Claude
(System Settings → Notifications → Claude), switch to another app, let Claude finish a reply so a
notification pops up, then run the probe again.

**Copy everything the probe prints** and send it back.

## 4. Run the critter

```bash
python3 desk_critter.pyw
```

A spider should appear at the bottom-right of the screen, above the Dock. Terminal stays busy while
it runs. To stop it, use **Quit** in the critter's menu, or press `Ctrl+C` in Terminal.

Check each of these:

| # | Try this | Expected |
|---|---|---|
| a | Look at the critter | Only the spider is visible, no box or coloured rectangle around it |
| b | Watch it for a few seconds | It bobs, blinks and waves its front legs |
| c | Move the mouse over it | It waves faster |
| d | Right-click it (or Control-click, or two-finger click) | A menu opens |
| e | Menu → **Critter** → pick each one | Spider, Robot, Cat, Owl and ESP32 board each appear |
| f | Menu → **Test ▸ Alert** | It bounces, turns red-orange and plays a sound |
| g | Menu → **Test ▸ Done (green eyes)** | Eyes turn green (robot and ESP32: lights pulse green) |
| h | Drag it somewhere else | It moves and stays there |
| i | Double-click it | The Claude app comes to the front |
| j | Menu → **Quit**, then run the command again | Same critter, same position as before |
| k | Menu → **Test ▸ Working (dots, 8 s)** | Three blue dots bounce above the critter for about 8 seconds |

## 5. A real notification

1. With the critter running, switch to another app (not Claude).
2. Let Claude finish a reply, so that a Claude notification pops up.
3. The critter should turn green-eyed (finished) or bounce red (Claude needs you).
4. Then run:

```bash
tail -n 20 desk_critter.log
```

Shows the last 20 lines of the critter's log.

## 6. Claude Code hooks: finished, needs you, working (new in v2.3 and v2.4)

Notifications only appear when Claude is not the app in front, and on the Mac they all seem to say
"Claude is waiting for your input", so the critter can't tell "finished" from "needs you". Hooks fix
both for Claude Code sessions (including the Code tab of the Claude app): Claude Code runs a small
script at each stage and the critter reacts, whatever app is in front. This is tested on Windows and
**not yet on a Mac**.

1. Find the full path of the code folder. In Terminal, inside that folder:

```bash
pwd
```

Prints the folder's full path, for example `/Users/you/Documents/Desk_Critter`.

2. Check the hook script runs. This writes one test line and should make a running critter's eyes go green:

```bash
echo '{}' | python3 critter_hook.py done
```

3. Open the Claude Code settings file in TextEdit (it is created if it doesn't exist):

```bash
mkdir -p ~/.claude && touch ~/.claude/settings.json && open -e ~/.claude/settings.json
```

4. Add the block below inside the outer `{ }` (if the file is empty, put `{` before it and `}` after
   it; if it already has settings, add a comma after the last one). Replace `/PATH/TO` with the path
   from step 1, in all five places. Save and close.

```json
"hooks": {
  "UserPromptSubmit": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "python3 \"/PATH/TO/critter_hook.py\" busy" } ] }
  ],
  "PostToolUse": [
    { "hooks": [ { "type": "command", "async": true,
                   "command": "python3 \"/PATH/TO/critter_hook.py\" tick" } ] }
  ],
  "Notification": [
    { "hooks": [ { "type": "command",
                   "command": "python3 \"/PATH/TO/critter_hook.py\" help" } ] }
  ],
  "Stop": [
    { "hooks": [ { "type": "command",
                   "command": "python3 \"/PATH/TO/critter_hook.py\" done" } ] }
  ],
  "SessionEnd": [
    { "hooks": [ { "type": "command",
                   "command": "python3 \"/PATH/TO/critter_hook.py\" end" } ] }
  ]
}
```

   The hook script needs no Tk, so plain `python3` is fine here even if the critter itself needs
   `python3.13`. If you later move or re-download the code folder, these paths must be updated.

5. With the critter running, use Claude Code and check:

| # | Do this | Expected |
|---|---|---|
| l | Send Claude Code a prompt that makes it run a few tools | Blue dots bounce above the critter while it works |
| m | Wait for it to finish, with Claude in front | Dots stop, eyes turn green for about 10 seconds |
| n | Trigger a permission prompt (ask it to run a command) | Critter bounces red and chimes |
| o | Approve the prompt | After the command has run, the dots come back |

6. Afterwards, show the hook lines in the log:

```bash
grep "Claude Code hook" desk_critter.log | tail -n 10
```

## What to report back

1. The macOS version (Apple menu → **About This Mac**).
2. Everything printed by the probe in step 3.
3. For step 4, which letters (a to k) worked and which didn't, and what you saw instead.
   A screenshot of the critter helps (`Cmd+Shift+4`, then drag over it).
4. The output of the `tail` command in step 5.
5. For step 6, which letters (l to o) worked, and the output of the `grep` command.
6. Any error text that appeared in Terminal.

## Getting fixes later

When a fix has been pushed, update your copy:

- **git in Terminal:** `git pull` inside the code folder downloads the latest version.
- **ZIP:** quit the critter, move the old `Desk_Critter-main` folder to the Trash, download the ZIP again
  and unpack it. Your chosen critter and position start fresh, because the settings file lived in the old folder.
- **GitHub Desktop:** click **Fetch origin**, then **Pull origin**.

Then run the critter again.

## Known differences from Windows

- There is no taskbar-flash backup trigger; notifications are the only trigger.
- The Dock height is a guess, so the starting position may be a little high or low. Drag it where
  you want it; the position is remembered.
- A critter left on a second display goes back to the corner after a restart.
- Python shows its own icon in the Dock while the critter runs.
- `tools/install.py` can copy a tagged version to `~/Tools/Desk_Critter`, but its `--startup`
  option (start at sign-in) is Windows only for now.
