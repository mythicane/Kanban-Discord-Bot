'''THE MAIN FUNCTION OF THE KANBAN DISCORD BOT!

Hello! I'm Kanban Bot- a (Python) Bot specializing in Kanban Style Project Management.
I'm specifically engineered for discord server based start-up tasking with the Six kanban
productivity practices in mind! The Kanban Discord Bot's goal is to reenforce the Six kanban
practices to maximize productivity when accomplishing tasks...

1. Visualize the workflow. The Kanban board visualizes a team’s workload in a way that’s
easy to understand and execute.

2. Limit work in progress. Restricting the number of tasks a team is working on at any
given time helps maintain focus.

3. Manage flow. This method switches the focus from managing people to managing a smooth
flow of work.

4. Make policies explicit. Keep them simple, visible, and easy to understand.

5. Use feedback loops. Revisiting project goals regularly helps the team respond to changes
 and take advantage of new opportunities.

6. Improve collaboratively. Teams with a shared vision can work together to achieve continuous
 improvement. These evolutions should be based on metrics and experimentation.

[Source: GOOGLE's Project Management Professional Certification via Coursea']

Copyright "Free Use" for educational/public/open source purposes under the MIT License.

If you use this discord bot for your project management needs or commercial purposes, please
make sure to credit 'Greta Perez Haiek' [user: @Mythicane via Github], and send her a message
on Linkedin! She would love to know how her discord bot helps you reach you or your team's goals :)

GIT: https://github.com/mythicane/Kanban-Discord-Bot'''

import os
import io
import datetime
from collections import defaultdict

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')  # render without a display -- this bot only ever saves to an in-memory buffer
import matplotlib.pyplot as plt

# ── credentials ──────────────────────────────────────────────────────────────
# Never hardcode a bot token in source. Put it in a local .env file instead
# (see .env.example / README.md) -- .env is gitignored so it never gets committed.
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

STATUSES = ['To Do', 'In Progress', 'Done']
PRIORITIES = ['low', 'mid', 'high']
PRIORITY_ORDER = {'high': 3, 'mid': 2, 'low': 1}

intents = discord.Intents.default()
# Message Content is a privileged intent -- must also be enabled for this bot
# in the Discord Developer Portal (Bot > Privileged Gateway Intents).
intents.message_content = True
intents.members = True

client = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ── data ─────────────────────────────────────────────────────────────────────
# Everything below is in-memory only -- restarting the bot clears all boards.
# Keyed by guild (server) ID so multiple servers can run against one bot instance.
kanban_boards = defaultdict(lambda: {status: [] for status in STATUSES})
task_details = defaultdict(dict)  # task_details[guild_id][task_name] -> dict


def _board(guild_id):
    return kanban_boards[guild_id]


def _details(guild_id):
    return task_details[guild_id]


def generate_kanban_image(board, details):
    '''Given a guild's kanban board + task details, renders the board as a PNG
    (via matplotlib) and returns an in-memory buffer -- nothing touches disk.'''
    fig, ax = plt.subplots(figsize=(10, 5))
    columns = STATUSES
    num_rows = max((len(board[col]) for col in columns), default=0)

    def sort_key(task):
        priority = details.get(task, {}).get('priority', 'low')
        return PRIORITY_ORDER.get(priority, 1)

    sorted_board = {col: sorted(board[col], key=sort_key, reverse=True) for col in columns}

    table_data = []
    for row in range(num_rows):
        row_data = []
        for col in columns:
            tasks_in_col = sorted_board[col]
            row_data.append(tasks_in_col[row] if row < len(tasks_in_col) else '')
        table_data.append(row_data)
    if not table_data:
        table_data = [['' for _ in columns]]

    table = ax.table(cellText=table_data, colLabels=columns, loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.2)

    ax.axis('tight')
    ax.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return buf


# ── startup / background reminders ────────────────────────────────────────────

@client.event
async def on_ready():
    print('Connected to bot: {}'.format(client.user.name))
    print('Bot ID: {}'.format(client.user.id))
    if not check_deadlines.is_running():
        check_deadlines.start()


@tasks.loop(minutes=15)
async def check_deadlines():
    '''Every 15 minutes, pings the assigned user (in DMs) for any task with
    notifications enabled that is within 24 hours of its deadline, or overdue.'''
    now = datetime.datetime.now()
    for guild_id, details in task_details.items():
        for task, info in details.items():
            if not info.get('notifications'):
                continue
            user = info.get('user')
            deadline = info.get('deadline')
            if user is None or deadline is None:
                continue
            if deadline >= now and (deadline - now).total_seconds() <= 3600 * 24:
                await user.send(f'Friendly Reminder: The deadline for task "{task}" is in less than a day!')
            elif deadline < now:
                await user.send(f'ALERT: The deadline for task "{task}" has passed!')


# ── commands ───────────────────────────────────────────────────────────────────

@client.command()
async def ping(ctx):
    '''A "test" command to make sure that the bot is responsive'''
    await ctx.send('Pong!')


@client.command()
async def add(ctx):
    '''Creates and adds a task to the KanBan board task dictionary, via a short Q&A.'''
    board = _board(ctx.guild.id)
    details = _details(ctx.guild.id)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    await ctx.send('Let’s add a task! What status would you like? Use "To Do", "In Progress", or "Done".')
    status_msg = await client.wait_for('message', check=check)
    status = status_msg.content.strip()
    if status not in board:
        await ctx.send('Invalid status! Use "To Do", "In Progress", or "Done". Type "!add" to try again.')
        return

    await ctx.send('What is your priority? Use "low", "mid", or "high".')
    priority_msg = await client.wait_for('message', check=check)
    priority = priority_msg.content.strip().lower()
    if priority not in PRIORITIES:
        await ctx.send('Invalid priority! Use "low", "mid", or "high". Type "!add" to try again.')
        return

    await ctx.send('What is your task?')
    task_msg = await client.wait_for('message', check=check)
    task = task_msg.content.strip()
    if not task:
        await ctx.send('Task name can\'t be empty. Type "!add" to try again.')
        return
    if task in details:
        await ctx.send(f'A task named "{task}" already exists on this board. Type "!add" to try again with a different name.')
        return

    await ctx.send('What is your deadline? Use the following format: "YYYY-MM-DD"')
    deadline_msg = await client.wait_for('message', check=check)
    try:
        deadline_date = datetime.datetime.strptime(deadline_msg.content.strip(), '%Y-%m-%d')
    except ValueError:
        await ctx.send('Invalid deadline format! Use "YYYY-MM-DD". Type "!add" to try again.')
        return

    await ctx.send('Who is responsible? Mention the user with @username.')
    user_msg = await client.wait_for('message', check=check)
    user = user_msg.mentions[0] if user_msg.mentions else None
    if not user:
        await ctx.send('Please mention a valid user. Type "!add" to try again.')
        return

    await ctx.send(f'Would {user.mention} like to receive notifications? [y/n]')
    response_msg = await client.wait_for('message', check=check)
    response = response_msg.content.strip().lower()
    if response == 'y':
        notification_bool = True
    elif response == 'n':
        notification_bool = False
    else:
        await ctx.send('Invalid response! Simply type "y" or "n". Type "!add" to try again.')
        return

    board[status].append(task)
    details[task] = {
        'user': user,
        'deadline': deadline_date,
        'notifications': notification_bool,
        'priority': priority,
        'checklist': [],
    }

    await ctx.send(f'Task "{task}" added to {status}, assigned to {user.mention}, with deadline {deadline_date.date()} and priority {priority}.')
    if notification_bool:
        await ctx.send(f'{user.mention} WILL be receiving reminders in their DMs within 24 hours of the deadline, and if it passes.')
    else:
        await ctx.send(f'{user.mention} will NOT be receiving reminders for this task.')


@client.command()
async def move(ctx, new_status: str, *, task: str):
    '''Moves a task to a new status column, e.g. !move "In Progress" Write Documentation.
    Moving to "Done" requires all checklist items (if any) to be completed first.'''
    board = _board(ctx.guild.id)
    details = _details(ctx.guild.id)

    if new_status not in board:
        await ctx.send('Invalid new status! Use "To Do", "In Progress", or "Done".')
        return

    if new_status == 'Done':
        checklist = details.get(task, {}).get('checklist', [])
        if checklist and not all(item['completed'] for item in checklist):
            await ctx.send(f'Cannot move "{task}" to "Done" -- not all checklist items are completed.\n_Psst... use `!list_checklist {task}` to see what\'s left!_')
            return

    for status in board:
        if task in board[status]:
            board[status].remove(task)
            board[new_status].append(task)
            await ctx.send(f'Task "{task}" moved to {new_status}.')
            return
    await ctx.send('Task not found! Perhaps you had a typo...?')


@client.command()
async def resolve(ctx, *, task: str):
    '''Shortcut for `!move "Done" <task>` -- marks a task resolved/complete.'''
    await move(ctx, 'Done', task=task)


@client.command(aliases=['delete'])
async def remove(ctx, *, task: str):
    '''Removes a task entirely from the board (all statuses) and deletes its details.'''
    board = _board(ctx.guild.id)
    details = _details(ctx.guild.id)

    found = False
    for status in board:
        if task in board[status]:
            board[status].remove(task)
            found = True
    details.pop(task, None)

    if found:
        await ctx.send(f'Task "{task}" removed from the board.')
    else:
        await ctx.send('Task not found! Perhaps you had a typo...?')


@client.command()
async def show(ctx):
    '''Prints out the KanBan board as an image.'''
    board = _board(ctx.guild.id)
    details = _details(ctx.guild.id)
    buf = generate_kanban_image(board, details)
    await ctx.send(file=discord.File(buf, 'kanban.png'))


@client.command(name='list_tasks', aliases=['list'])
async def list_tasks(ctx):
    '''Lists every task on the board, grouped by status, as text (not an image).'''
    board = _board(ctx.guild.id)
    details = _details(ctx.guild.id)
    embed = discord.Embed(title=f'Kanban Board — {ctx.guild.name}')

    for status in STATUSES:
        rows = []
        for task in sorted(board[status], key=lambda t: PRIORITY_ORDER.get(details.get(t, {}).get('priority', 'low'), 1), reverse=True):
            info = details.get(task, {})
            assigned_user = info.get('user')
            assigned = assigned_user.mention if isinstance(assigned_user, discord.abc.User) else 'Unassigned'
            deadline = info.get('deadline')
            deadline_str = deadline.strftime('%Y-%m-%d') if deadline else 'No deadline'
            priority = info.get('priority', 'low')
            checklist = info.get('checklist', [])
            checklist_str = f"{sum(item['completed'] for item in checklist)}/{len(checklist)} checklist items" if checklist else 'no checklist'
            notif = 'notifications on' if info.get('notifications') else 'notifications off'
            rows.append(f'**{task}** — {assigned}, due {deadline_str}, priority: {priority}, {checklist_str}, {notif}')
        embed.add_field(name=f'{status} ({len(board[status])})', value='\n'.join(rows) or 'No tasks.', inline=False)

    await ctx.send(embed=embed)


@client.command()
async def set_priority(ctx, priority: str, *, task: str):
    '''Sets the priority of an existing task -- e.g. !set_priority high Write Documentation.'''
    priority = priority.lower()
    if priority not in PRIORITIES:
        await ctx.send('Invalid priority! Use "low", "mid", or "high".')
        return
    details = _details(ctx.guild.id)
    if task not in details:
        await ctx.send('Task not found!')
        return
    details[task]['priority'] = priority
    await ctx.send(f'Priority for task "{task}" set to {priority}.')


@client.command()
async def enable_notifications(ctx, *, task: str):
    '''Enables deadline reminders for a task you're assigned to.'''
    details = _details(ctx.guild.id)
    info = details.get(task)
    if info and info.get('user') == ctx.author:
        info['notifications'] = True
        await ctx.send(f'Notifications enabled for task "{task}".')
    else:
        await ctx.send('You are not assigned to this task, or the task does not exist.')


@client.command()
async def disable_notifications(ctx, *, task: str):
    '''Disables deadline reminders for a task you're assigned to.'''
    details = _details(ctx.guild.id)
    info = details.get(task)
    if info and info.get('user') == ctx.author:
        info['notifications'] = False
        await ctx.send(f'Notifications disabled for task "{task}".')
    else:
        await ctx.send('You are not assigned to this task, or the task does not exist.')


@client.command()
async def add_checklist(ctx, task: str, *, item: str):
    '''Adds a checklist sub-item under a task -- e.g. !add_checklist "Write Documentation" Draft outline.'''
    details = _details(ctx.guild.id)
    if task not in details:
        await ctx.send('Task not found!')
        return
    details[task].setdefault('checklist', []).append({'item': item, 'completed': False})
    await ctx.send(f'Checklist item "{item}" added to task "{task}".')


@client.command()
async def complete_checklist(ctx, task: str, *, item: str):
    '''Marks a checklist sub-item as completed.'''
    details = _details(ctx.guild.id)
    if task not in details:
        await ctx.send('Task not found!')
        return
    for checklist_item in details[task].get('checklist', []):
        if checklist_item['item'] == item:
            checklist_item['completed'] = True
            await ctx.send(f'Checklist item "{item}" marked as completed for task "{task}".')
            return
    await ctx.send('Checklist item not found!')


@client.command()
async def list_checklist(ctx, *, task: str):
    '''Lists the checklist items under a task.'''
    details = _details(ctx.guild.id)
    if task not in details:
        await ctx.send('Task not found!')
        return
    checklist = details[task].get('checklist', [])
    if not checklist:
        await ctx.send(f'No checklist items for "{task}".\n_Psst... add one with `!add_checklist {task} <item>`!_')
        return
    lines = [f"{item['item']} — {'Completed' if item['completed'] else 'Incomplete'}" for item in checklist]
    await ctx.send(f'Checklist for task "{task}":\n' + '\n'.join(lines))


@client.command()
async def about(ctx):
    '''Prints a little bit of information about the KanBan Discord Bot.'''
    about_text = (
        "Hello! I'm Kanban Bot- a (Python) Bot specializing in Kanban Style Project Management. I'm specifically engineered for discord server based start-up tasking with the Six kanban productivity practices in mind! The Kanban Discord Bot's goal is to reenforce the Six kanban practices to maximize productivity when accomplishing tasks...\n"
        "\n"
        "1. _Visualize the workflow. The Kanban board visualizes a team’s workload in a way that’s easy to understand and execute._ \n"
        "2. _Limit work in progress. Restricting the number of tasks a team is working on at any given time helps maintain focus._ \n"
        "3. _Manage flow. This method switches the focus from managing people to managing a smooth flow of work._ \n"
        "4. _Make policies explicit. Keep them simple, visible, and easy to understand._ \n"
        "5. _Use feedback loops. Revisiting project goals regularly helps the team respond to changes and take advantage of new opportunities._ \n"
        "6. _Improve collaboratively. Teams with a shared vision can work together to achieve continuous improvement. These evolutions should be based on metrics and experimentation._ \n"
        "[Source: GOOGLE's Project Management Professional Certification via Coursea']. \n"
        "\n"
        "**Copyright 'Free Use' for educational/public/open source purposes under the MIT License.** \n"
        "\n"
        "If you use this discord bot for your project management needs or commercial purposes, please make sure to credit 'Greta Perez Haiek' [user: @Mythicane via Github], and send her a message on Linkedin! She would love to know how her discord bot helps you reach you or your team's goals :) \n"
        "\n"
        "GIT: https://github.com/mythicane/Kanban-Discord-Bot \n"
    )
    await ctx.send(about_text)


@client.command(name='help')
async def help_command(ctx):
    '''Lists all available commands and what they do.'''
    help_text = (
        "**Kanban Bot Commands**\n\n"
        "`!add` — add a task, via a short guided Q&A (status, priority, task, deadline, assignee, notifications).\n"
        "`!move <new_status> <task>` — move a task to a new status, e.g. `!move \"In Progress\" Write Documentation`.\n"
        "`!resolve <task>` — shortcut for moving a task to \"Done\".\n"
        "`!remove <task>` (alias `!delete`) — remove a task from the board entirely.\n"
        "`!show` — show the current Kanban board as an image.\n"
        "`!list_tasks` (alias `!list`) — list all tasks in the Kanban board as text.\n"
        "`!set_priority <priority> <task>` — set a task's priority (low/mid/high).\n"
        "`!add_checklist <task> <item>` — add a checklist item to a task.\n"
        "`!complete_checklist <task> <item>` — mark a checklist item completed.\n"
        "`!list_checklist <task>` — list a task's checklist items.\n"
        "`!enable_notifications <task>` / `!disable_notifications <task>` — toggle deadline DM reminders for a task you're assigned to.\n"
        "`!about` — learn more about the Kanban philosophy this bot is built around.\n"
        "`!ping` — check that the bot is responsive.\n"
        "`!help` — show this message.\n"
        "\n"
        "_Thank you for reading... Happy Tasking! :)_"
    )
    await ctx.send(help_text)


if __name__ == '__main__':
    if not TOKEN or TOKEN in ('INSERT_YOUR_TOKEN_HERE', '{your-bot-token}'):
        raise SystemExit(
            'No Discord bot token found. Create a .env file (see .env.example) '
            'with DISCORD_TOKEN=<your token> -- see README.md for how to get one.'
        )
    client.run(TOKEN)
