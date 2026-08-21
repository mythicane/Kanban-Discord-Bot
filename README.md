# Kanban Discord Bot

A (Python) Discord Bot specializing in Kanban-style project management —
built for organizations running task tracking directly out of a Discord
server. Add tasks, assign owners and deadlines, track priority and
checklists, move tasks across a To Do / In Progress / Done board, and get DM
reminders as deadlines approach.

The bot reinforces the six Kanban practices:

1. **Visualize the workflow.** The Kanban board visualizes a team's workload
   in a way that's easy to understand and execute.
2. **Limit work in progress.** Restricting the number of tasks a team is
   working on at any given time helps maintain focus.
3. **Manage flow.** This method switches the focus from managing people to
   managing a smooth flow of work.
4. **Make policies explicit.** Keep them simple, visible, and easy to
   understand.
5. **Use feedback loops.** Revisiting project goals regularly helps the team
   respond to changes and take advantage of new opportunities.
6. **Improve collaboratively.** Teams with a shared vision can work together
   to achieve continuous improvement.

[Source: Google's Project Management Professional Certification via Coursera]

## Setup — run this bot with your own token

This repo contains **no token** — every user runs their own instance of the
bot under their own Discord Application, so nobody shares credentials.

1. **Create a Discord Application + Bot** at the
   [Discord Developer Portal](https://discord.com/developers/applications):
   New Application → Bot → Reset Token (copy it — you won't see it again) →
   under **Privileged Gateway Intents**, enable **Message Content Intent**
   (this bot's commands require it).
2. **Invite the bot to your server**: Developer Portal → OAuth2 → URL
   Generator → scopes `bot`, permissions `Send Messages`, `Embed Links`,
   `Attach Files`, `Read Message History` → open the generated URL and pick
   your server.
3. **Clone this repo and install dependencies:**
   ```bash
   git clone https://github.com/mythicane/Kanban-Discord-Bot.git
   cd Kanban-Discord-Bot
   pip install -r requirements.txt
   ```
4. **Add your token.** Copy `.env.example` to `.env` and paste in the token
   from step 1:
   ```bash
   cp .env.example .env
   # then edit .env: DISCORD_TOKEN=your-actual-token
   ```
   `.env` is gitignored — it will never be committed. **Never paste a real
   token into `Main.py` or any tracked file.**
5. **Run it:**
   ```bash
   python Main.py
   ```
   If `DISCORD_TOKEN` isn't set, the bot exits immediately with a reminder
   instead of failing with a cryptic Discord login error.

Board state (tasks, assignees, deadlines, checklists) is currently held
**in memory per server** — restarting the bot clears it. That's a natural
next improvement if you want persistence (e.g. a JSON file or a database)
across restarts.

## Commands

| Command | Description |
|---|---|
| `!add` | Add a task via a short guided Q&A (status, priority, task, deadline, assignee, notifications). |
| `!move <new_status> <task>` | Move a task to a new status, e.g. `!move "In Progress" Write Documentation`. |
| `!resolve <task>` | Shortcut for moving a task to "Done". |
| `!remove <task>` (alias `!delete`) | Remove a task from the board entirely. |
| `!show` | Render the current Kanban board as an image. |
| `!list_tasks` (alias `!list`) | List all tasks, grouped by status, as text. |
| `!set_priority <priority> <task>` | Set a task's priority (`low`/`mid`/`high`). |
| `!add_checklist <task> <item>` | Add a checklist item to a task. |
| `!complete_checklist <task> <item>` | Mark a checklist item completed. |
| `!list_checklist <task>` | List a task's checklist items. |
| `!enable_notifications <task>` / `!disable_notifications <task>` | Toggle deadline DM reminders for a task you're assigned to. |
| `!about` | Learn more about the Kanban philosophy behind this bot. |
| `!ping` | Check that the bot is responsive. |
| `!help` | Show all commands in Discord. |

Moving a task to "Done" (via `!move` or `!resolve`) is blocked until every
checklist item on that task is marked complete, if it has any.

Every 15 minutes, the bot DMs the assigned user for any task (with
notifications enabled) that's within 24 hours of its deadline, or overdue.

## License

MIT — see `LICENSE`.

If you use this discord bot for your project management needs or
commercial/private purposes, credit 'Greta Perez Haiek' [user: @Mythicane via
Github], and send her a message on LinkedIn! She would love to know how the
"Kanban" discord bot helped you or your team reach your goals :)

GIT: https://github.com/mythicane/Kanban-Discord-Bot
