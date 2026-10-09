# ChronoCrash Modders Tools - Project Structure

This document describes the file and folder structure of the ChronoCrash Modders Tools project, including areas of responsibility for each component.

## Root Level Files

| File | Purpose |
| ---- | ------- |
| `cmt.py` | Main entry point for the application |
| `commandgen.py` | Command-line interface for command generation |
| `debug.py` | Debugging utilities |
| `debugApp.py` | Application-level debugging tools |
| `debugXML.py` | XML debugging utilities |
| `deleteSave.py` | Utility script for deleting save data |
| `dialogeditor.py` | Dialog/form editor component |
| `fallbackicons.py` | Fallback icon resources when primary icons unavailable |
| `fallbackiconsold.py` | Legacy fallback icon resources |
| `imagewidget.py` | Image display widget |
| `modales.py` | Modal dialog components |
| `mugen.py` | MUGEN-related functionality |
| `pak.py` | Package/archive handling |
| `reset-data.py` | Utility script to reset application data |
| `spritesorter.py` | Sprite organization and sorting tool |
| `style.py` | Application styling and theming |
| `tools.py` | General utility tools |
| `volnorm.py` | Volume normalization audio tool |
| `oxygen.qrc` | Qt resource file for Oxygen theme icons |
| `linux_build.sh` | Build script for Linux distributions |
| `__init__.py` | Python package initialization |

## Directory Structure

### `/common/` - Shared Utilities & Configuration

**Responsibility:** Cross-cutting concerns and shared functionality used throughout the application.

| File | Purpose |
| ---- | ------- |
| `settings.py` | Application settings management and configuration |
| `util.py` | General-purpose utility functions |
| `messager.py` | Messaging/notification system |
| `xdg.py` | XDG Base Directory specification implementation (cross-platform paths) |
| `~` files | Backup/temporary versions of configuration files |

### `/data/` - Data Handling & Persistence

**Responsibility:** Data access layer, database operations, and data model definitions.

| File | Purpose |
| ---- | ------- |
| `db.py` | Database interface and data persistence |

### `/gui/` - Graphical User Interface Components

**Responsibility:** All GUI windows, dialogs, and visual components. Organized by functional domain.

**Main Files:**

| File | Purpose |
| ---- | ------- |
| `menubar.py` | Main application menu bar |
| `util.py` | GUI-specific utility functions |
| `modales.py` | Modal dialog windows |
| `commandgen.py` | Command generation GUI |
| `comparefiles.py` | File comparison interface |
| `fontpreview.py` | Font preview widget |
| `imagewidget.py` | Image display and manipulation widget |
| `orphans.py` | Orphaned/unreferenced asset viewer |
| `pak.py` | Package/archive management interface |
| `portrait.py` | Portrait editor for character sprites |
| `volnorm.py` | Volume normalization interface |
| `mugen.py` | MUGEN-specific editor interface |

**Subdirectories:**

- `main/` - Main application window and core UI structure
- `project/` - Project management and file handling UI
- `entity/` - Entity editor (characters, objects) GUI
- `level/` - Level editor GUI
- `settings/` - Settings and preferences dialog
- `json_editor/` - JSON file editor interface
- `backupviewer/` - Backup file viewer interface

### `/guilib/` - GUI Library Components

**Responsibility:** Reusable GUI widgets and custom controls.

| File | Purpose |
| ---- | ------- |
| `title_box.py` | Custom titled box widget |
| `treemodel.py` | Tree data model for hierarchical display |

### `/icons/` - Icon Resources

**Responsibility:** All visual assets and icon management.

| File/Folder | Purpose |
| ---- | ------- |
| `icons.py` | Icon resource loader and manager |
| `CMT.png` | Application logo |
| `*.svg` | Scalable vector icons (undo, redo, save, etc.) |
| `*.png` | Raster icon images |
| `32x32/` | 32-pixel resolution icon variants |
| `64x64/` | 64-pixel resolution icon variants |
| `oxygen/` | Oxygen theme icon set |
| `oxygen.qrc` | Qt resource file for Oxygen icons |

### `/oki/` - Configuration Storage

**Responsibility:** Persistent storage of user settings and application state.

- `settings/` - User preference files
- `data/` - Cached or persistent data files

### `/other/` - External Tools & Resources

**Responsibility:** Third-party tools and temporary files (not part of core application).

| Item | Purpose |
| ---- | ------- |
| `i_view32.exe` | External image viewer (Windows) |
| `i_view32.ini` | ImageView configuration |
| `sffextract.exe` | SFF (Sprite Format) extraction tool |
| `Juggernaut_MvC/` | Sample data for testing |
| `dolf/` | Sample project data |
| `*.txt` | Temporary output/log files |

### `/qutepart/` - Text Editor Widget (Current)

**Responsibility:** Main code editor implementation with syntax highlighting, bookmarks, and vim support.

| File | Purpose |
| ---- | ------- |
| `syntaxhlighter.py` | Syntax highlighting engine |
| `completer.py` | Code completion system |
| `brackethlighter.py` | Bracket/brace matching highlighter |
| `rectangularselection.py` | Multi-line rectangular selection |
| `sideareas.py` | Line numbers, bookmarks, margins |
| `margins.py` | Margin display |
| `vim.py` | Vim keybinding support |
| `bookmarks.py` | Bookmark management |
| `htmldelegate.py` | HTML rendering delegate |
| `lines.py` | Line management |
| `debug.py` | Debug utilities for editor |
| `version.py` | Version information |
| `icons/` | Editor-specific icons |
| `indenter/` | Indentation handling |
| `syntax/` | Syntax definition files |

### `/qutepart-mine/` - Text Editor Widget (Custom Fork)

**Responsibility:** Local customized version of qutepart with modifications.

Similar structure to `/qutepart/` with user-specific modifications.

### `/qutepart-new-orig/` & `/qutepart-old/` - Text Editor Widget (Archived Versions)

**Responsibility:** Version history and backups of the text editor widget.

Older/alternate implementations maintained for reference or fallback.

### `/templates/` - Document Templates

**Responsibility:** Template files for creating new documents (levels, entities, scripts, etc.).

### `/themes/` - Visual Themes

**Responsibility:** Application themes, stylesheets, and appearance configurations.

## Architecture Overview

### Entry Points

- **Main Application:** `cmt.py` - Initializes the main GUI window
- **Command-Line Tools:** Various root-level `.py` files for specific utilities

### Layered Architecture

1. **Presentation Layer:** `/gui/` - User interface components
2. **UI Library:** `/guilib/` - Reusable controls
3. **Business Logic:** `/common/`, individual utilities
4. **Data Layer:** `/data/` - Database and persistence
5. **Resources:** `/icons/`, `/templates/`, `/themes/`

### Dependencies Flow

```bash
Root Entry (cmt.py)
  ├── GUI Components (gui/)
  │   ├── GUI Library (guilib/)
  │   ├── Text Editor (qutepart/)
  │   └── Icons (icons/)
  ├── Common Utilities (common/)
  └── Data Layer (data/)
```

## File Naming Conventions

- **Python files:** lowercase with underscores (`file_name.py`)
- **Backup files:** original name with `~` suffix (`file.py~`)
- **Icon files:** descriptive lowercase names (`.svg`, `.png`)
- **Resource files:** `.qrc` (Qt resource format)

## Development Guidelines

### When Adding New Features

1. **GUI Feature?** → Create in appropriate `/gui/` subdirectory
2. **Utility Function?** → Add to `/common/util.py` or create new module in `/common/`
3. **New Icon?** → Place in `/icons/` and register in `icons.py`
4. **Configuration?** → Add to `/common/settings.py`
5. **Data Model?** → Add to `/data/db.py`

### Backup and Temporary Files

- Backup files (`.py~`) exist for reference but shouldn't be committed
- Temporary files in `/other/` may be generated during development

### Cross-Platform Compatibility

- Use `/common/xdg.py` for file system paths
- Use `/common/settings.py` for configuration
- Ensure Linux and Windows compatibility

---

**Last Updated:** 2026-10-09  
**Project:** ChronoCrash Modders Tools  
**Language:** Python 3 + Qt5
