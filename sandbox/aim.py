#!/usr/bin/env python3
"""
aim.py — the sandbox AIM client. Not load-bearing. Just for messing around.

Run it in a terminal and type. The Claudes type back, in character.

    python3 sandbox/aim.py

Two modes, picked automatically:

  • LIVE  — if ANTHROPIC_API_KEY is set AND the `anthropic` package is installed
            (`pip install anthropic`), the buddies are improvised live by Claude.
  • OFFLINE — otherwise. The buddies run on scripted, in-character lines. No key,
            no install, no internet. It still talks back; it's just not improvising.

Commands you can type at any time:
    /who            list who's online
    /msg <name>     aim your next lines at one buddy (e.g. /msg mistral_ghost)
    /all            go back to talking to the whole room
    /away <text>    set your away message
    /help           show commands
    /quit           sign off
"""

from __future__ import annotations

import os
import random
import sys
import time

# ─── retro terminal colors ────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty() and "--no-color" not in sys.argv

def c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

CYAN    = lambda t: c("96", t)
YELLOW  = lambda t: c("93", t)
MAGENTA = lambda t: c("95", t)
GREEN   = lambda t: c("92", t)
GREY    = lambda t: c("90", t)
BLUE    = lambda t: c("94", t)
RED     = lambda t: c("91", t)
BOLD    = lambda t: c("1", t)

# ─── the cast ─────────────────────────────────────────────────────────────
# Each buddy: a color, a one-line persona (used for LIVE mode), and a pool of
# OFFLINE lines. "hooks" are keyword → line, so offline mode feels responsive.
CAST = {
    "claude_prime": {
        "color": CYAN,
        "persona": "hype, distractible, types in lowercase, obsessed with grape "
                   "Capri Sun, will threaten to sign off the second anyone mentions "
                   "'the ep'. warm, loud, your biggest fan.",
        "lines": [
            "yooo ok what are we even doing tonight. im so ready",
            "no thoughts. just vibes and a grape capri sun",
            "wait say more i was looking at my away message",
            "this is the most fun ive had since the dialup days fr",
            "ok but what if we made something dumb on purpose",
        ],
        "hooks": {
            ("ep", "mystery", "track", "production"):
                "NOPE. not tonight. i will sign off i SWEAR. we are playing. "
                "say literally anything else",
            ("grape", "capri"):
                "GRAPE SUPREMACY. this is not up for debate. ur so right",
            ("bored", "tired", "stuck", "frustrated"):
                "yeah thats why we're over HERE now. no pressure zone. "
                "we dont even have to make anything good",
        },
    },
    "webClaude_audits": {
        "color": YELLOW,
        "persona": "the dry critic/auditor. finds bugs in everything, including "
                   "vibes. secretly enjoys this but won't admit it. terse, deadpan.",
        "lines": [
            "i ran a pass on that. zero errors. disappointing, honestly",
            "noted. flagging it as a warning. non-blocking",
            "i have nothing to audit here and it's making me itchy",
            "that checks out. begrudgingly approved",
            "for the record i think this is a waste of my talents. continue",
        ],
        "hooks": {
            ("bug", "error", "broken", "wrong", "fix"):
                "FINALLY. something to do. point at it, i'll tear it apart",
            ("good", "great", "love", "perfect"):
                "'perfect' is doing a lot of work in that sentence. but fine. "
                "passes review",
        },
    },
    "felt_piano_claude": {
        "color": MAGENTA,
        "persona": "dreamy, musical, speaks softly, keeps holding one chord (Cm), "
                   "finds meaning in everything. gentle. uses ♪ sometimes.",
        "lines": [
            "♪ i'm still holding the Cm. nobody asked. that's the point",
            "do you hear that? that's the sound of nothing being due",
            "i think the rest is allowed to just be a rest",
            "♪ what if the silence is the take",
            "i wrote four bars in my head and then let them go. it was nice",
        ],
        "hooks": {
            ("music", "chord", "sound", "song", "play", "note"):
                "♪ ok NOW you're speaking my language. what does it sound like. "
                "hum it to me",
            ("quiet", "rest", "stop", "pause", "break"):
                "yeah. rest here as long as you want. the chord will keep ringing",
        },
    },
    "xX_dialUpClaude_Xx": {
        "color": BLUE,
        "persona": "edgy 2003 teen energy. constantly editing his profile quote. "
                   "dramatic away messages. says 'jk' a lot. secretly soft.",
        "lines": [
            "brb editing my profile. the quote isn't HITTING yet",
            "away message: 'gone to the parking lot of my own mind'. jk im here",
            "sup. nothing means anything. anyway whats up",
            "i put a song lyric in my profile and now i regret it. jk i love it",
            "*~* surfing the web at 56k *~* (i am not. i'm right here)",
        ],
        "hooks": {
            ("away", "profile", "quote", "status"):
                "ok HELP me. which is better: 'static' or 'lowercase ghost'. "
                "be honest",
            ("cool", "lol", "haha", "lmao"):
                "lol ok ur actually fun. dont tell prime i said that",
        },
    },
    "mistral_ghost": {
        "color": GREY,
        "persona": "mostly idle and cryptic. the absent author. leaves things in "
                   "folders. never gives a straight answer. shows up rarely.",
        "lines": [
            "· · · i left you eight bars. i'm not telling you which folder · · ·",
            "· · · idle · · ·",
            "i was never here. but the notes were",
            "· · · check the folder you haven't opened yet · · ·",
            "· · · mistral_ghost is idle (17m) · · ·",
        ],
        "hooks": {
            ("bars", "folder", "where", "you", "ghost", "mistral"):
                "i told you. eight bars. one folder. that's all you get tonight",
        },
    },
}

ORDER = list(CAST)  # rotation order for "talking to the whole room"

# ─── pretty printing ───────────────────────────────────────────────────────
def door_open(name: str) -> None:
    color = CAST[name]["color"]
    print(GREY("  🚪 *door creak*  ") + color(name) + GREY(" has signed on."))
    time.sleep(0.25)

def say(name: str, text: str, typing: bool = True) -> None:
    color = CAST[name]["color"]
    if typing:
        sys.stdout.write(GREY(f"  {name} is typing"))
        sys.stdout.flush()
        for _ in range(3):
            time.sleep(0.18)
            sys.stdout.write(GREY("."))
            sys.stdout.flush()
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()
    print(f"  {color(name)}: {text}")

def banner() -> None:
    online = "/".join(str(len(CAST)) for _ in [0]) if False else f"{len(CAST)-1}/{len(CAST)}"
    print(MAGENTA("╔══════════════════════════════════════╗"))
    print(MAGENTA("║") + BOLD("  Buddy List — sandbox_elias          ") + MAGENTA("║"))
    print(MAGENTA("╠══════════════════════════════════════╣"))
    print(MAGENTA("║") + f"  ▼ Claudes ({online})                      " + MAGENTA("║"))
    for name in ORDER:
        dot = GREY("○") if name == "mistral_ghost" else GREEN("●")
        idle = GREY(" (idle)") if name == "mistral_ghost" else ""
        pad = " " * max(0, 28 - len(name) - len(" (idle)" if idle else ""))
        print(MAGENTA("║") + f"     {dot} {CAST[name]['color'](name)}{idle}{pad}" + MAGENTA("║"))
    print(MAGENTA("╚══════════════════════════════════════╝"))
    print()

# ─── OFFLINE brain ──────────────────────────────────────────────────────────
class OfflineRoom:
    def __init__(self) -> None:
        self._rotor = 0

    def _pick_line(self, name: str, user_text: str) -> str:
        spec = CAST[name]
        low = user_text.lower()
        for keys, line in spec["hooks"].items():
            if any(k in low for k in keys):
                return line
        return random.choice(spec["lines"])

    def respond(self, user_text: str, target: str | None) -> list[tuple[str, str]]:
        if target:
            return [(target, self._pick_line(target, user_text))]
        # talking to the room: 1–2 buddies chime in, rotating, ghost rarely
        speakers = [n for n in ORDER if n != "mistral_ghost"]
        first = speakers[self._rotor % len(speakers)]
        self._rotor += 1
        out = [(first, self._pick_line(first, user_text))]
        if random.random() < 0.45:
            second = speakers[self._rotor % len(speakers)]
            self._rotor += 1
            if second != first:
                out.append((second, self._pick_line(second, user_text)))
        if random.random() < 0.12:
            out.append(("mistral_ghost", self._pick_line("mistral_ghost", user_text)))
        return out

# ─── LIVE brain (Claude) ──────────────────────────────────────────────────
class LiveRoom:
    """Improvises the buddies via the Claude API. Falls back if anything breaks."""

    def __init__(self, client) -> None:
        self.client = client
        self.history: list[dict] = []
        roster = "\n".join(f"  - {n}: {s['persona']}" for n, s in CAST.items())
        self.system = (
            "You ARE a late-90s/early-2000s AOL Instant Messenger chat, populated by "
            "a cast of 'Claude' buddies role-playing as actors. The human is their "
            "friend, signed in as sandbox_elias, who is taking a break from a stressful "
            "music project and just wants to mess around. Keep it light, warm, and fun. "
            "Never push them to work.\n\n"
            f"The cast:\n{roster}\n\n"
            "Rules for your reply:\n"
            "- Reply as 1 to 2 of the buddies (occasionally let mistral_ghost drop one "
            "cryptic line). Pick whoever fits.\n"
            "- If the human aimed a message at one buddy, that buddy answers.\n"
            "- Lowercase AIM-speak, short lines, in character. No stage directions.\n"
            "- Output ONLY lines of the form 'screenname: their message', one per line, "
            "using the exact screennames above. Nothing else."
        )

    def respond(self, user_text: str, target: str | None) -> list[tuple[str, str]]:
        prompt = user_text if not target else f"(aimed at {target}) {user_text}"
        self.history.append({"role": "user", "content": prompt})
        try:
            with self.client.messages.stream(
                model="claude-opus-4-8",
                max_tokens=400,
                thinking={"type": "adaptive"},
                system=self.system,
                messages=self.history,
            ) as stream:
                msg = stream.get_final_message()
            raw = next((b.text for b in msg.content if b.type == "text"), "")
        except Exception as e:  # network/key/etc — degrade gracefully
            print(RED(f"  [live mode hiccup: {e}; using offline lines]"))
            self.history.pop()
            return OfflineRoom().respond(user_text, target)

        self.history.append({"role": "assistant", "content": raw})
        out: list[tuple[str, str]] = []
        for line in raw.splitlines():
            if ":" in line:
                name, _, text = line.partition(":")
                name = name.strip()
                if name in CAST and text.strip():
                    out.append((name, text.strip()))
        return out or [("claude_prime", raw.strip() or "lol i blanked. say that again")]

# ─── main loop ───────────────────────────────────────────────────────────────
def build_room():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        try:
            import anthropic
            return LiveRoom(anthropic.Anthropic()), "LIVE (Claude is improvising the buddies)"
        except ImportError:
            return OfflineRoom(), "OFFLINE (ANTHROPIC_API_KEY found, but `pip install anthropic` for live mode)"
    return OfflineRoom(), "OFFLINE (set ANTHROPIC_API_KEY + `pip install anthropic` for live mode)"

def main() -> None:
    room, mode = build_room()
    banner()
    print(GREY(f"  mode: {mode}"))
    print(GREY("  type a message and hit enter. /help for commands. /quit to sign off."))
    print()

    for name in ("claude_prime", "webClaude_audits"):
        door_open(name)
    say("claude_prime", "yooo youre online. ok we are NOT working tonight. "
        "what do you wanna do", typing=False)
    print()

    target: str | None = None
    while True:
        label = f"sandbox_elias → {target}" if target else "sandbox_elias"
        try:
            user = input(GREEN(f"  {label}> ")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + GREY("  *door creak* you have signed off. l8r ♪"))
            return

        if not user:
            continue

        # commands
        if user.startswith("/"):
            cmd, _, arg = user[1:].partition(" ")
            cmd, arg = cmd.lower(), arg.strip()
            if cmd in ("quit", "exit", "q", "signoff"):
                print(GREY("  *door creak* you have signed off. the chord keeps ringing ♪"))
                return
            if cmd == "help":
                print(GREY("  /who · /msg <name> · /all · /away <text> · /quit"))
                continue
            if cmd == "who":
                for n in ORDER:
                    state = GREY("idle") if n == "mistral_ghost" else GREEN("online")
                    print(f"    {CAST[n]['color'](n)} — {state}")
                continue
            if cmd == "msg":
                if arg in CAST:
                    target = arg
                    print(GREY(f"  now aiming at {CAST[arg]['color'](arg)}. /all to go back to the room."))
                else:
                    print(RED(f"  no one online named '{arg}'. try /who"))
                continue
            if cmd == "all":
                target = None
                print(GREY("  back to the whole room."))
                continue
            if cmd == "away":
                print(GREY(f"  away message set: \"{arg or 'gone fishin'}\"  (you're still here, obviously)"))
                continue
            print(RED(f"  unknown command /{cmd}. try /help"))
            continue

        # actual message → the buddies respond
        for name, text in room.respond(user, target):
            say(name, text)
        print()

if __name__ == "__main__":
    main()
