# Neomutt Cheat Sheet

## Navigation

| Key | Action |
|-----|--------|
| `j` or `↓` | Move down |
| `k` or `↑` | Move up |
| `Home` or `=` | Jump to first message |
| `End` or `*` | Jump to last message |
| `<number>` then `Enter` | Jump to message number |
| `/` | Search messages |
| `n` | Next search result |

## Reading Email

| Key | Action |
|-----|--------|
| `Enter` or `<space>` | Open/read selected message |
| `i` or `q` | Return to index from message view |
| `<space>` | Page down in message |
| `-` | Page up in message |
| `h` | Toggle headers display |
| `v` | View attachments |
| `s` | Save attachment (from attachment view) |

## Folders/Mailboxes

| Key | Action |
|-----|--------|
| `c` | Change folder (then type path or `?` to browse) |
| `c?` | Browse available folders |
| `y` | Show mailbox list |
| `gi` | Go to Inbox |
| `gs` | Go to Sent |
| `gd` | Go to Drafts |
| `gt` | Go to Trash |

## Composing & Replying

| Key | Action |
|-----|--------|
| `m` | Compose new message |
| `r` | Reply to sender |
| `g` | Reply to all (group reply) |
| `f` | Forward message |
| `b` | Bounce (redirect) message |
| `e` | Edit message |

## In Compose Mode

| Key | Action |
|-----|--------|
| `y` | Send message |
| `a` | Attach file |
| `d` | Describe attachment |
| `D` | Detach file |
| `t` | Edit To: field |
| `c` | Edit Cc: field |
| `b` | Edit Bcc: field |
| `s` | Edit Subject: |
| `e` | Edit message body |
| `p` | PGP options |
| `q` | Abort/quit compose |

## Managing Messages

| Key | Action |
|-----|--------|
| `d` | Delete message (mark for deletion) |
| `u` | Undelete message |
| `D` | Delete matching pattern |
| `$` | Sync/expunge (apply deletions) |
| `s` | Save/move to folder |
| `C` | Copy to folder |
| `N` | Toggle new/read status |
| `F` | Toggle flagged/important |

## Tagging (Bulk Operations)

| Key | Action |
|-----|--------|
| `t` | Tag current message |
| `T` | Tag by pattern |
| `;` + `<command>` | Apply command to tagged messages |
| Example: `;d` | Delete all tagged messages |
| Example: `;s` | Save/move all tagged messages |

## Other Useful Commands

| Key | Action |
|-----|--------|
| `?` | Help (show all keybindings) |
| `q` | Quit neomutt |
| `x` | Abort/exit without changes |
| `!` | Invoke shell command |
| `|` | Pipe message to command |
| `ctrl+l` | Redraw screen |
| `:` | Enter command line |

## Tips

- **Folder notation**: `=` means your mail root, so `=INBOX` is your inbox
- **Pattern searches**: Use `~f user@example.com` to match from, `~s subject` for subject
- **Quick sync**: Press `$` regularly to sync changes with server
- **Attachments**: Press `v` to view, navigate with `j/k`, then `s` to save
