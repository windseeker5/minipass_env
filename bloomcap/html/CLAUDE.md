# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a static HTML website template called "webphil" - a landing page template for SaaS, startup, and agency websites. It's built with pure HTML, CSS, and JavaScript without any build tools or package managers.

## Project Structure

The project follows a traditional static website structure:

- **Root HTML files**: Multiple landing page variations (index.html, home-*.html, portfolio-*.html, etc.)
- **CSS**: Located in `/css/` directory
  - `main.css`: Primary stylesheet with component-based organization
  - `bootstrap.css`: Bootstrap framework styles
- **JavaScript**: Located in `/js/` directory
  - `custom.js`: Main custom functionality
  - `menu.js`: Navigation menu functionality
- **Images**: Organized in `/image/` directory with subdirectories for different sections
- **Plugins**: Third-party libraries in `/plugins/` directory
- **Fonts**: Custom fonts and icon fonts in `/fonts/` directory

## Key Architecture Details

### CSS Organization
The main.css file uses a component-based approach with CSS custom properties for theming:
- Light/dark theme support via CSS variables
- Component sections: Header, Menu, Button, Lists, Background, Form, Cards, Modal, Tab, Accordion, Sidebar
- Responsive design with mobile-first approach

### JavaScript Architecture
- jQuery-based with multiple plugins for functionality
- Modular approach with separate files for different features
- Plugin dependencies: AOS (animations), Slick (sliders), Fancybox (lightbox), etc.

### Template Variations
Multiple homepage layouts available:
- Marketing (`home-marketing.html`)
- IT Services (`home-it-services.html`)
- Agency (`home-agency.html`)
- Digital Agency (`home-digital-agency.html`)
- Project Management (`home-project-management.html`)
- Services (`home-services.html`)
- App Presenting (`home-app.html`)
- Startup (`home-startup.html`)

## Development Guidelines

### Working with HTML Files
- The main entry point is `index.html`
- Each HTML file is self-contained with its own content
- Navigation menus are embedded in each file and need to be updated across all files when modified
- Forms use action="https://finestwp.co/" (external service)

### Working with CSS
- Main styles are in `css/main.css`
- Theme switching is handled via CSS custom properties
- Bootstrap classes are used throughout for responsive layout
- Icon fonts are custom (Grayic) and FontAwesome 5

### Working with JavaScript
- No build process - files are directly included in HTML
- jQuery is the main dependency
- Custom functionality is in `js/custom.js`
- Menu interactions are handled in `js/menu.js`

### Asset Management
- Images are organized by section in `/image/` subdirectories
- SVG icons are in `/image/svg/`
- No image optimization or build process
- All assets are referenced with relative paths

## Common Tasks

Since this is a static site with no build tools:
- **Making changes**: Edit HTML, CSS, or JS files directly
- **Adding new pages**: Copy an existing HTML file and modify content
- **Updating navigation**: Must be done manually across all HTML files
- **Testing**: Open HTML files directly in browser
- **Deployment**: Upload all files to web server

## Important Notes

- No package.json or build process - this is a template for static deployment
- All external links currently point to "https://finestwp.co/" (template provider)
- Template includes placeholder content that needs customization
- Multiple color themes and layout variations are available
- All JavaScript functionality works without a server