# Gemini Computer Use Reference

*Dec 2025 Specifications*

## Overview

Browser control agent enabling Gemini to "see" (screenshot) and "act" (click/type).

## Model

**MUST** use `gemini-2.5-computer-use-preview-10-2025`.

## Architecture (Client Logic Required)

1. **Request**: Send User Prompt + Current Screenshot.
2. **Response**: Model returns `FunctionCall` (e.g., `click_at`, `type_text_at`) + optional `safety_decision`.
3. **Execute**: Client (Playwright/Selenium) performs action.
    * *If `safety_decision="require_confirmation"`, MUST prompt user.*
4. **Capture**: Take new screenshot.
5. **Loop**: Send result + new screenshot back.

## Supported Actions

`open_web_browser`, `click_at`, `type_text_at`, `scroll_document`, `drag_and_drop`, `go_back`, etc.
Coordinate system: 1000x1000 grid.

## Safety

DO NOT use for:
* Bypassing CAPTCHAs.
* Accepting Terms of Service / Cookie Banners (User confirmation required).
* Financial transactions.
