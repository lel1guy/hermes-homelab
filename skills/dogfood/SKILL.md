---
name: dogfood
description: "Exploratory QA of web apps: find bugs, evidence, reports."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [qa, testing, browser, web, dogfood]
---

# Dogfood: Systematic Web Application QA Testing

## Overview

This skill guides you through systematic exploratory QA testing of web applications using the browser toolset. You will navigate the application, interact with elements, capture evidence of issues, and produce a structured bug report.

## Prerequisites

- Browser toolset must be available (`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type`, `browser_vision`, `browser_console`, `browser_scroll`, `browser_back`, `browser_press`)
- A target URL and testing scope from the user

## Workflow

### Phase 1: Plan

1. Create the output directory structure:
   ```
   {output_dir}/
   ├── screenshots/       # Evidence screenshots
   └── report.md          # Final report
   ```

2. Review the target URL and scope to plan testing areas

### Phase 2: Explore

Navigate the application systematically:
- Test all navigation paths
- Interact with all UI elements (buttons, forms, links)
- Test edge cases in inputs (empty, very long, special chars)
- Check error states and empty states

### Phase 3: Investigate

For each area, use the browser tools:
- `browser_vision` to inspect visual layout
- `browser_console` to check for JS errors and API failures
- `browser_snapshot` for accessibility tree issues
- Capture screenshots of issues with `browser_vision`

### Phase 4: Document

For each bug found, document:
- **Title**: Clear, descriptive
- **Severity**: Critical / Major / Minor / Cosmetic
- **Steps to Reproduce**: Numbered list
- **Expected vs Actual**: What should happen vs what does
- **Environment**: Browser, OS
- **Evidence**: Screenshot path

### Phase 5: Report

Generate a structured markdown report with:
- Summary of test scope
- Bug count by severity
- Full bug details
- Overall assessment and recommendations