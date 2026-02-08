# Twenty CRM Setup Guide for Minipass

**For total beginners** - Follow each step exactly as written.

---

# PART 1: UNDERSTANDING TWENTY CRM

## What You See When You Open Twenty

When you go to `http://localhost:3000` and log in, you see:

```
┌─────────────────────────────────────────────────────────────┐
│  [Search bar]                                    [Settings] │
├──────────┬──────────────────────────────────────────────────┤
│          │                                                  │
│ SIDEBAR  │              MAIN AREA                           │
│          │                                                  │
│ Search   │   This is where your records appear              │
│ ────────│   (like a spreadsheet or board)                  │
│ People   │                                                  │
│ Companies│                                                  │
│ Opport.. │                                                  │
│ Tasks    │                                                  │
│ Notes    │                                                  │
│          │                                                  │
│ ────────│                                                  │
│ Settings │                                                  │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

## The 4 Things You Need to Know

| Word | What It Means | Your Example |
|------|---------------|--------------|
| **Object** | A category of things you track | "Campaign" is an object |
| **Record** | One specific thing in that category | "Bundle Explainer Video" is one Campaign record |
| **Field** | A piece of information about a record | Status, Platform, Start Date are fields |
| **Task** | An action item you can assign to someone | "Record the video" assigned to Elizabeth |

## What Comes Built-In (You Don't Create These)

Twenty already has these objects ready to use:
- **People** - Individual contacts
- **Companies** - Organizations
- **Opportunities** - Sales deals
- **Tasks** - Action items (can be linked to any record)
- **Notes** - Written notes (can be linked to any record)

## What You Need to Create

You need to create ONE custom object:
- **Campaign** - To track your marketing ideas and execution

---

# PART 2: CREATE YOUR CAMPAIGN OBJECT

## Step 1: Open Settings

1. Look at the **bottom-left corner** of your screen
2. Click the **gear icon** (⚙️ Settings)
3. A settings panel opens on the left side

**What you see now:**
```
Settings
├── Profile
├── Experience
├── Accounts
└── Workspace
    ├── General
    ├── Members
    ├── Data model  ← CLICK THIS
    ├── Integrations
    └── ...
```

## Step 2: Open Data Model

1. Under "Workspace", click **Data model**
2. You see a list of objects: People, Companies, Opportunities, Notes, Tasks

**What you see now:**
```
Data model
─────────────────────────────────
Objects                [+ New object]  ← THIS BUTTON
─────────────────────────────────
📧 People
🏢 Companies
💰 Opportunities
📝 Notes
✓ Tasks
```

## Step 3: Create the Campaign Object

1. Click the **+ New object** button (top-right area)
2. A form appears. Fill it in EXACTLY like this:

| Field | What to Type |
|-------|--------------|
| **Singular name** | `Campaign` |
| **Plural name** | `Campaigns` |
| **Description** | `Marketing campaign ideas, planning, and execution` |

3. Click the **icon selector** and pick an icon you like (megaphone, target, etc.)
4. Click **Save** (top-right)

**Success!** Your Campaign object now appears in the sidebar.

## Step 4: Add Fields to Your Campaign Object

Now you need to add fields so you can store information about each campaign.

1. In the Data model list, click on **Campaign** (the one you just created)
2. You see a page showing Campaign's fields (it starts with just a Name field)
3. Click **+ Add field** button

### Field 1: Status

This field tracks where the campaign is in your workflow.

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Status`
   - **Type**: Click dropdown → Select **Select**
3. After selecting "Select", you see "Options" section
4. Add these options (click + to add each):
   - `Idea`
   - `Approved`
   - `In Progress`
   - `Completed`
   - `Cancelled`
5. Click **Save**

### Field 2: Platform

Where will this campaign be published?

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Platform`
   - **Type**: **Select**
3. Add options:
   - `Instagram`
   - `Facebook`
   - `LinkedIn`
   - `TikTok`
   - `YouTube`
   - `Website`
   - `Email`
5. Click **Save**

### Field 3: Goal

What do you want to achieve with this campaign?

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Goal`
   - **Type**: **Long Text** (for multiple lines)
3. Click **Save**

### Field 4: Start Date

When should this campaign launch?

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Start Date`
   - **Type**: **Date**
3. Click **Save**

### Field 5: Links

For attaching documents, videos, or references.

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Resources`
   - **Type**: **Links**
3. Click **Save**

### Field 6: Assigned To (Relation)

Who is responsible for this campaign?

1. Click **+ Add field**
2. Fill in:
   - **Name**: `Assigned To`
   - **Type**: **Relation**
3. When you select Relation, you choose which object to link to:
   - Select **People**
4. Click **Save**

## Step 5: Verify Your Setup

Your Campaign object should now have these fields:
- Name (built-in)
- Status (Select)
- Platform (Select)
- Goal (Long Text)
- Start Date (Date)
- Resources (Links)
- Assigned To (Relation to People)

---

# PART 3: SET UP A KANBAN VIEW FOR CAMPAIGNS

A Kanban view shows your campaigns as cards organized by Status (like a board).

## Step 1: Go to Campaigns

1. Click **Campaigns** in the left sidebar
2. You see an empty table view

## Step 2: Create a Kanban View

1. Look at the top of the main area - you see a dropdown that says "All Campaigns" or similar
2. Click that dropdown
3. Click **+ Add view**
4. A form appears:
   - **Name**: `Campaign Board`
   - **View type**: Select **Kanban**
5. Click **Create**

## Step 3: Configure the Kanban

1. You now see a board with columns
2. The board automatically uses your "Status" field for columns:
   ```
   | Idea | Approved | In Progress | Completed | Cancelled |
   |------|----------|-------------|-----------|-----------|
   |      |          |             |           |           |
   ```

**Done!** Now when you create campaigns, they appear as cards you can drag between columns.

---

# PART 4: ADD YOUR FIRST TEAM MEMBER

Before creating your real example, let's add Elizabeth so you can assign work to her.

## Step 1: Add Elizabeth as a Person Record

1. Click **People** in the left sidebar
2. Click **+ New person** (or just **+** button)
3. Fill in:
   - **First name**: `Elizabeth`
   - **Last name**: (her last name)
   - **Email**: (her email)
4. Press Enter or click Save

## Step 2: Invite Elizabeth to Twenty (Optional)

If you want Elizabeth to log into Twenty herself:

1. Click **Settings** (gear icon, bottom-left)
2. Click **Members** (under Workspace)
3. Click **Invite**
4. Enter Elizabeth's email
5. She receives an invite to create her account

---

# PART 5: REAL EXAMPLE - YOUR FIRST CAMPAIGN

Let's create your real campaign: **"Bundle/Tiers Explainer Video"**

## The Scenario

- **Your idea**: Create a video explaining the Minipass bundles and pricing tiers
- **Goal**: Help potential customers understand what they're buying
- **Platform**: Could be YouTube, Instagram, or Website
- **Assigned to**: Elizabeth

## Step 1: Create the Campaign Record

1. Click **Campaigns** in the left sidebar
2. Click the **+ New campaign** button (or just **+**)
3. A form appears on the right side of the screen

Fill in these fields:

| Field | Value |
|-------|-------|
| **Name** | `Bundle & Tiers Explainer Video` |
| **Status** | `Idea` |
| **Platform** | `YouTube` (or wherever you want to post it) |
| **Goal** | `Create a clear video explaining our 3 pricing tiers and bundles. Help customers understand what Pass Credits are, what each tier includes, and which tier is right for them.` |
| **Start Date** | Leave empty for now (you'll set it when approved) |
| **Resources** | Leave empty for now |
| **Assigned To** | Click and search for `Elizabeth` |

4. Press Enter or click away to save

**Your campaign is created!**

## Step 2: Add a Note for Discussion

Notes are perfect for brainstorming and team discussion.

1. Click on your new campaign "Bundle & Tiers Explainer Video" to open it
2. Look for the **Notes** section or tab
3. Click **+ Add note**
4. Write your thoughts:

```
Initial Ideas for this video:

1. Start with "What is Minipass?" - 30 seconds
2. Show the 3 tiers side by side
3. Explain Pass Credits with a visual example
4. End with "Which tier is right for you?" decision tree

Questions for team:
- Should we use animation or screen recording?
- Who should narrate?
- What's our target length? 2 minutes?

Let me know your thoughts!
- Kevin
```

5. Save the note

## Step 3: Create Tasks for Elizabeth

Tasks are specific action items with due dates and assignees.

1. With the campaign still open, look for the **Tasks** section or tab
2. Click **+ Add task**
3. Create this task:

| Field | Value |
|-------|-------|
| **Title** | `Review video idea and share feedback` |
| **Assignee** | `Elizabeth` |
| **Due date** | (pick a date, like 3 days from now) |

4. Add more tasks:

**Task 2:**
| Field | Value |
|-------|-------|
| **Title** | `Write video script draft` |
| **Assignee** | `Elizabeth` |
| **Due date** | (1 week from now) |

**Task 3:**
| Field | Value |
|-------|-------|
| **Title** | `Record video` |
| **Assignee** | `Elizabeth` |
| **Due date** | (2 weeks from now) |

**Task 4:**
| Field | Value |
|-------|-------|
| **Title** | `Edit and publish video` |
| **Assignee** | `Elizabeth` |
| **Due date** | (3 weeks from now) |

## Step 4: Add Resource Links

Once Elizabeth creates documents or videos, add them here:

1. Open the campaign
2. Find the **Resources** field
3. Click to edit
4. Add links like:
   - `https://docs.google.com/document/d/xxx` (script document)
   - `https://drive.google.com/file/xxx` (video file)
   - `https://canva.com/design/xxx` (thumbnail design)

---

# PART 6: THE WORKFLOW - FROM IDEA TO DONE

Here's how your team will use this system:

## Week 1: Idea Stage

1. **Anyone** creates a Campaign with Status = "Idea"
2. They add a Note explaining the idea
3. They might assign a Task: "Review this idea by Friday"

## Weekly Team Meeting

1. Open the **Campaign Board** (Kanban view)
2. Look at all cards in the "Idea" column
3. Discuss each idea
4. Decision:
   - **Keep developing** → Add more tasks, keep in "Idea"
   - **Approve it** → Drag card to "Approved" column
   - **Not now** → Drag to "Cancelled" or leave in "Idea"

## When Approved

1. Drag the card to **Approved**
2. Set the **Start Date**
3. Create specific **Tasks** with due dates
4. Assign tasks to team members

## During Execution

1. Drag to **In Progress** when work begins
2. Team members complete their Tasks (check them off)
3. Add Notes for updates and decisions
4. Add **Resources** links as materials are created

## When Complete

1. Drag to **Completed**
2. Add a final Note with results/learnings
3. Celebrate!

---

# PART 7: QUICK REFERENCE

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Search anything | `/` or `Cmd+K` (Mac) / `Ctrl+K` (Windows) |
| Create new record | `Cmd+K` then type what you want |

## Common Actions

| I want to... | Do this... |
|--------------|------------|
| Create a new campaign | Click Campaigns → Click + |
| Add a task to a campaign | Open campaign → Tasks section → + Add task |
| Add a note to a campaign | Open campaign → Notes section → + Add note |
| Move campaign to new status | Drag the card on the Kanban board |
| Assign someone | Edit the "Assigned To" field → Search their name |
| Add a document link | Edit the "Resources" field → Paste URL |

## Where Things Are

| Thing | Location |
|-------|----------|
| Settings | Gear icon, bottom-left |
| Data model (to edit fields) | Settings → Workspace → Data model |
| Invite team members | Settings → Workspace → Members |
| Your objects | Left sidebar |
| Switch views | Dropdown at top of main area |

---

# WHAT'S NEXT?

Once you're comfortable with Campaigns, you can add more custom objects:

1. **Competitor** - Track competitive intelligence
2. **Segment** - Track market segments you're targeting

But start with Campaign first. Get comfortable with creating records, adding tasks, and moving things through your Kanban board. Then expand.

---

# TROUBLESHOOTING

## "I don't see the + Add field button"

Make sure you:
1. Are in Settings → Data model
2. Clicked on the specific object (Campaign)
3. Look for the button near the field list

## "I can't assign Elizabeth to a campaign"

Make sure you:
1. Created Elizabeth as a Person first (People → + New)
2. Created the "Assigned To" field as a Relation to People

## "My Kanban board has no columns"

Make sure you:
1. Created the Status field with Select type
2. Added the options (Idea, Approved, etc.)
3. The Kanban view uses a Select field for columns

## "I need help"

- Twenty Docs: https://docs.twenty.com
- Twenty Discord: https://discord.gg/twenty

---

# SUMMARY CHECKLIST

## Setup (Do Once)

- [ ] Open Twenty at `http://localhost:3000`
- [ ] Go to Settings → Data model
- [ ] Create Campaign object
- [ ] Add fields: Status, Platform, Goal, Start Date, Resources, Assigned To
- [ ] Create a Kanban view called "Campaign Board"
- [ ] Add team members as People records
- [ ] (Optional) Invite team members to Twenty

## For Each New Campaign Idea

- [ ] Create Campaign record with Status = "Idea"
- [ ] Add a Note explaining the idea
- [ ] Assign to someone for review
- [ ] Discuss in team meeting
- [ ] If approved: set Start Date, create Tasks, drag to "Approved"
- [ ] Track progress through Kanban columns
- [ ] Add Resource links as materials are created
- [ ] Mark complete when done

---

*Guide created for Minipass team - January 2026*
*Based on Twenty CRM official documentation*
