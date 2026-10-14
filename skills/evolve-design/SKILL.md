---
name: evolve-design
description: Investigate and improve actual product flows, interaction design, accessibility and visual consistency in an existing application. Use for an authorised interface or UX improvement, modernisation, customisation work, or the design stage of Evolve.
---

# Evolve Design

Improve users' ability to complete their work and implement a coherent interface.
Honour critique-only requests. Preserve established editing/workflow capabilities
unless the user's task changes them.

## Shared resources

Load sibling `evolve`, or resolve it next to this skill, and read
[design](../evolve/references/design.md) and
[verification](../evolve/references/verification.md). If unavailable, follow the
procedure below and report missing UI access or evidence tools.

## Procedure

1. Capture the actual interface and representative workflows before judging it.
   Inspect navigation, hierarchy, density, feedback, keyboard access, focus,
   resizing and the states relevant to the task. Use synthetic content.
2. Explain the user problem and define observable success. Separate usability
   problems, accessibility failures and visual preferences. Prioritise recurring
   workflow friction over decoration.
3. Inspect the current component/token system. Define the minimum coherent
   changes to typography, spacing, colours, icons, surfaces and interactions.
   Account for themes, contrast, localisation and platform conventions.
4. Implement through real application state. For customisation, include saved
   preferences, validation, defaults, reset behaviour and compatibility/migration
   as required. Keep the core workflow discoverable.
5. Inspect before/after captures under comparable viewport, content and state.
   Check empty/loading/error/long-content states and relevant light/dark modes.
   Use actual interaction checks for focus and keyboard behaviour; screenshots
   alone cannot establish accessibility or persistence.
6. Return implemented behaviour, inspected artifacts, checks and remaining limits.
   Request independent verification for substantial changes.

Use original or appropriately licensed assets. Respect reduced motion and avoid
animation that delays input or hides state. Do not replace working functionality
with a decorative mockup or declare a redesign polished without inspecting it.
