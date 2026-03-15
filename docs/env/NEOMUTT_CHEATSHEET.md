# Neomutt Cheat Sheet — Email Client

## Launch
```bash
neomutt                   # Open neomutt
neomutt -f /path/mailbox  # Open specific mailbox
```

---

## Navigation (Index — email list)
| Key | Action |
|-----|--------|
| `j / k` | Next / Previous email |
| `g g` | Go to first email |
| `G` | Go to last email |
| `Enter` | Open email |
| `q` | Quit / Go back |
| `Tab` | Jump to next unread |
| `Ctrl+f` | Page down |
| `Ctrl+b` | Page up |

---

## Reading Email (Pager)
| Key | Action |
|-----|--------|
| `Space` | Scroll down |
| `j / k` | Scroll line by line |
| `q` | Back to index |
| `h` | Toggle headers |
| `v` | View attachments |
| `Enter` | Open attachment |

---

## Folders / Mailboxes
| Key | Action |
|-----|--------|
| `c` | Change mailbox (type `?` to list) |
| `c ?` | Browse mailbox list |
| `c !` | Jump to inbox |
| `y` | Open mailbox list |
| `q` | Back |

---

## Email Actions
| Key | Action |
|-----|--------|
| `m` | Compose new email |
| `r` | Reply to sender |
| `R` | Reply all |
| `f` | Forward email |
| `d` | Delete email |
| `u` | Undelete email |
| `s` | Save email to folder |
| `C` | Copy email to folder |
| `$` | Sync / purge deleted |

---

## Composing Email
| Key | Action |
|-----|--------|
| `m` | New email |
| Fill `To:`, `Subject:` | Type and press `Enter` |
| Editor opens | Write your email |
| `:wq` | Save and return (if vim/nvim) |
| `y` | Send the email |
| `q` | Abort / cancel |
| `a` | Attach a file |

---

## Search & Filter
| Key | Action |
|-----|--------|
| `/` | Search emails |
| `l` | Limit view (filter) |
| `l all` | Show all emails again |
| `l ~N` | Show only unread |
| `l ~F` | Show only flagged |

---

## Common Limit Patterns
```
l ~N          # Unread
l ~F          # Flagged
l ~s word     # Subject contains "word"
l ~f user     # From contains "user"
l ~d <7d      # Last 7 days
l all         # Reset / show all
```

---

## Flags & Tagging
| Key | Action |
|-----|--------|
| `F` | Flag / unflag email |
| `t` | Tag email |
| `T` | Tag by pattern |
| `;` | Apply action to tagged |

---

## Config File
```bash
~/.neomuttrc          # Main config
~/.config/neomutt/    # Alt config location
```

### Useful config lines
```bash
set editor = "nvim"                  # Use neovim to compose
set sort = reverse-date              # Newest first
set sidebar_visible = yes            # Show folder sidebar
set sidebar_width = 25
set mail_check = 60                  # Check mail every 60s
```

---

## Sidebar Navigation (if enabled)
| Key | Action |
|-----|--------|
| `Ctrl+n` | Next folder in sidebar |
| `Ctrl+p` | Previous folder |
| `Ctrl+o` | Open selected folder |
| `B` | Toggle sidebar |

---

## Quit
| Key | Action |
|-----|--------|
| `q` | Quit current view |
| `Q` | Quit neomutt entirely |
