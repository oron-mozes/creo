# Creo Architecture

> **Multi-Agent Influencer Marketing Platform**

This document describes the core architecture of the Creo multi-agent system, including workflow stages, session state management, and memory architecture.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Stage Architecture](#workflow-stage-architecture)
3. [Session State Management](#session-state-management)
4. [Onboarding Agent Memory](#onboarding-agent-memory)
5. [API Reference](#api-reference)

---

## Overview

Creo is a multi-agent system built on Google's Agent Development Kit (ADK) for influencer marketing campaigns. The system uses:

- **Workflow stages** to coordinate multiple specialized agents
- **Shared state** for cross-agent communication
- **Agent-specific state** for internal agent logic
- **Type-safe enums** for workflow stages and states

### Key Components

- **SessionManager**: Manages user sessions and InMemoryRunners
- **SessionMemory**: Handles shared and agent-specific state
- **Workflow Stages**: Coordinate agent transitions
- **Specialized Agents**: onboarding, campaign_brief, creator_finder, outreach_message, campaign_builder

---

## Workflow Stage Architecture

### The Problem

When a user confirmed business details with "yes", the orchestrator would:
1. Intercept the confirmation
2. Immediately switch to `campaign_brief_agent`
3. Never let `onboarding_agent` respond with BUSINESS_CARD_CONFIRMATION block
4. Result: Business card was NOT saved

**Root Cause**: The orchestrator had no mechanism to enforce "stay with the current agent until it signals completion".

### The Solution: Workflow Stage Enforcement

The workflow stage mechanism ensures proper agent coordination by:
- Tracking which workflow stage is currently active
- Preventing premature agent switching
- Only transitioning stages when completion signals are detected

### Workflow Stages

All workflow stages are defined in `workflow_enums.py`:

```python
class WorkflowStage(str, Enum):
    ONBOARDING = "onboarding"
    CAMPAIGN_BRIEF = "campaign_brief"
    CREATOR_FINDER = "creator_finder"
    OUTREACH_MESSAGE = "outreach_message"
    CAMPAIGN_BUILDER = "campaign_builder"
```

### Stage Flow

```
┌─────────────┐     Business card     ┌────────────────┐
│             │      confirmed         │                │
│  ONBOARDING ├───────────────────────>│ CAMPAIGN_BRIEF │
│             │                        │                │
└─────────────┘                        └────────┬───────┘
                                                │ Brief created
                                                v
┌─────────────┐     Messages         ┌────────────────┐
│             │       drafted         │                │
│  CAMPAIGN   │<──────────────────────┤ CREATOR_FINDER │
│  BUILDER    │                       │                │
│             │                       └────────────────┘
└─────────────┘                                │
      ^                                        │ Creators
      │                                        │ identified
      │         ┌────────────────┐            │
      │         │                │            │
      └─────────┤ OUTREACH_      │<───────────┘
                │ MESSAGE        │
                └────────────────┘
```

### How It Works

#### 1. Initial Stage Selection (New Session)

```
User: "I need help finding influencers for my coffee shop"
  ↓
Orchestrator checks:
  - workflow_state.stage = None (new session)
  - business_card = None (no business card yet)
  ↓
Orchestrator sets:
  - workflow_state.stage = WorkflowStage.ONBOARDING
  ↓
Orchestrator calls: onboarding_agent
```

#### 2. Stage Enforcement (Active Stage)

```
User: "yes" (confirming business details)
  ↓
Orchestrator checks:
  - workflow_state.stage = WorkflowStage.ONBOARDING
  ↓
Orchestrator MUST call: onboarding_agent
  (even though user just confirmed - stay in stage!)
  ↓
Onboarding agent responds:
  "Perfect! Thanks for confirming..."
  BUSINESS_CARD_CONFIRMATION: {...}
  ↓
Orchestrator sees BUSINESS_CARD_CONFIRMATION
  ↓
Orchestrator transitions:
  - workflow_state.stage = WorkflowStage.CAMPAIGN_BRIEF
```

#### 3. Stage Transitions

Only the orchestrator can transition stages when it sees completion signals:

| Current Stage | Completion Signal | Next Stage |
|---------------|-------------------|------------|
| `ONBOARDING` | `BUSINESS_CARD_CONFIRMATION` block | `CAMPAIGN_BRIEF` |
| `CAMPAIGN_BRIEF` | Brief completed | `CREATOR_FINDER` |
| `CREATOR_FINDER` | Creators identified | `OUTREACH_MESSAGE` |
| `OUTREACH_MESSAGE` | Messages drafted | `CAMPAIGN_BUILDER` |
| `CAMPAIGN_BUILDER` | Campaign complete | `None` (end) |

### Orchestrator Rules

1. **ALWAYS check `workflow_state.stage` FIRST**
2. **If stage is set, route to that stage's agent** - no exceptions
3. **Do NOT switch agents until completion signal appears**
4. **Only orchestrator can transition stages** - agents can't
5. **Detect completion signals in agent responses** to trigger transitions

---

## Session State Management

### Architecture Principles

The Creo system separates **shared state** (accessible to all agents) from **agent-specific state** (private to each agent).

### Shared State

**Location**: `session_memory.shared_context`

**Purpose**: Information that ALL agents need to access

**Contents**:
- `session_id` - Session identifier
- `user_id` - User identifier (e.g., `google_123456` or `anon_abc123`)
- `user_profile` - User profile information from OAuth
  - `name` - User's full name (for personalization)
  - Empty dict `{}` for anonymous users
- `messages` - Full conversation history (ALL messages from all agents)
- `business_card` - Final confirmed business information
- `workflow_state.stage` - Current workflow stage
- `metadata` - Session-level metadata

**Access**: Any agent can read and write to shared context

### Agent-Specific State

**Location**: `session_memory.agent_contexts[agent_name]`

**Purpose**: Internal state that ONLY that agent needs

**Contents** (per agent):
- `onboarding_agent`:
  - `status` - Internal onboarding status (collecting, awaiting_confirmation, complete)
  - `extractions` - History of what was extracted, when, and from where
  - `extracted_fields` - Current extracted values (quick lookup)

- `creator_finder_agent`:
  - `search_history` - Past creator searches
  - `filters` - Applied search filters

- `campaign_brief_agent`:
  - `briefs` - Draft campaign briefs
  - `templates` - Brief templates

**Access**: Only that specific agent can access its own context

### Visual Architecture

```
SessionMemory
├── shared_context (SHARED - all agents can access)
│   ├── session_id
│   ├── user_id                        ← "google_123456" or "anon_abc123"
│   ├── user_profile {}                ← OAuth profile (name only) or {}
│   ├── messages []                    ← ALL messages
│   ├── business_card {}               ← Final confirmed data
│   ├── workflow_state
│   │   └── stage                      ← Current workflow stage
│   └── metadata {}
│
└── agent_contexts (AGENT-SPECIFIC - private to each agent)
    ├── onboarding_agent
    │   ├── status                     ← Internal onboarding state
    │   ├── extractions []             ← What was extracted, when, from where
    │   └── extracted_fields {}        ← Current extracted values
    │
    ├── creator_finder_agent
    │   ├── search_history []
    │   └── filters {}
    │
    ├── campaign_brief_agent
    │   ├── briefs []
    │   └── templates {}
    │
    └── ... other agents
```

### User Profile vs Business Card

**User Profile** (`user_profile`):
- Source: OAuth authentication (Google, etc.)
- Contains: User's name only (for personalization)
- Populated: Automatically for authenticated users
- Purpose: Personal identity for greeting/personalization
- Example: `{'name': 'John Doe'}`
- Anonymous users: Empty dict `{}`
- Privacy: Email and picture NOT stored in shared context

**Business Card** (`business_card`):
- Source: Onboarding agent extraction
- Contains: Business name, website, social links, location, service type
- Populated: Through conversation with onboarding agent
- Purpose: Business/brand information for influencer campaigns
- Example: `{'name': 'Alma Cafe', 'location': 'Rehovot, Israel', ...}`
- Before onboarding: `None`

**Key Difference**: User profile is about WHO the person is (name). Business card is about WHAT business they represent.

### Why This Separation?

#### 1. Encapsulation
Each agent manages its own internal state without exposing implementation details to other agents.

**Example**: The onboarding agent tracks extractions internally. Other agents don't need to know HOW information was collected, only the final result (business card).

#### 2. Scalability
As we add more agents, they can maintain their own state without cluttering the shared context.

#### 3. Clear Contracts
Shared context defines the "contract" between agents - what information is guaranteed to be available.

#### 4. Reduces Cognitive Load
Agents only need to understand their own state + the shared state, not every other agent's internal state.

### Data Flow Example

#### Phase 1: Information Collection (Agent-Specific)

```
User: "My website is https://almacafe.co.il"
  ↓
Onboarding Agent extracts:
  - Records to agent_contexts['onboarding_agent']['extractions']:
    [
      {field: 'website', value: 'https://almacafe.co.il', source: 'user_input'},
      {field: 'name', value: 'Alma Cafe', source: 'google_search'},
      {field: 'location', value: 'Rehovot, Israel', source: 'google_search'},
    ]
  - Sets agent_contexts['onboarding_agent']['status'] = OnboardingStatus.AWAITING_CONFIRMATION
```

**Visibility**: Only onboarding agent can see this extraction history.

#### Phase 2: User Confirmation (Transition to Shared)

```
User: "yes, that's correct"
  ↓
Onboarding Agent generates BUSINESS_CARD_CONFIRMATION block
  ↓
Server parses and saves to shared_context['business_card']:
  {
    'name': 'Alma Cafe',
    'website': 'https://almacafe.co.il',
    'location': 'Rehovot, Israel',
    'service_type': 'Coffee shop',
    'social_links': 'Not provided'
  }
```

**Visibility**: NOW all agents can see the business card in shared context.

#### Phase 3: Other Agents Use Shared Data

```
Campaign Brief Agent needs to personalize message:
  ↓
Reads shared_context['business_card']
  ↓
Uses business_card['name'] → "Alma Cafe"
  ↓
Generates: "Let's build a campaign for Alma Cafe..."
```

### Decision Matrix: Where to Store Data?

| Data Type | Storage Location | Reason |
|-----------|------------------|--------|
| Conversation messages | `shared_context['messages']` | All agents need conversation history |
| Business card (final) | `shared_context['business_card']` | All agents need business info for personalization |
| Workflow stage | `shared_context['workflow_state']['stage']` | Orchestrator needs to know current stage |
| Onboarding extractions | `agent_contexts['onboarding_agent']['extractions']` | Only onboarding agent needs extraction tracking |
| Onboarding status | `agent_contexts['onboarding_agent']['status']` | Only onboarding agent needs internal status |
| Creator search history | `agent_contexts['creator_finder_agent']['search_history']` | Only creator finder needs search history |
| Campaign briefs (drafts) | `agent_contexts['campaign_brief_agent']['briefs']` | Only campaign brief agent needs drafts |

---

## Onboarding Agent Memory

The onboarding agent has its own **agent-specific memory** for tracking what business card information has been extracted during the session.

### Purpose

1. **Track what fields have been extracted** - Avoid asking for the same information twice
2. **Record extraction sources** - Know if information came from user input, Google search, or inference
3. **Link extractions to messages** - Understand when each piece of information was collected
4. **Maintain extraction history** - See the full timeline of information gathering

### Memory Structure

The onboarding agent's context in `agent_contexts['onboarding_agent']`:

```python
{
    'status': OnboardingStatus.COLLECTING,  # Current onboarding status
    'extractions': [                         # Full extraction history
        {
            'field': 'name',
            'value': 'Alma Cafe',
            'message_id': 'msg_abc123',
            'source': 'google_search',
            'timestamp': '2025-01-16T10:30:00.000000'
        },
        # ... more extraction records
    ],
    'extracted_fields': {                    # Current extracted values (quick lookup)
        'name': 'Alma Cafe',
        'location': 'Rehovot, Israel',
        'service_type': 'Coffee shop',
    }
}
```

### Extraction Record Fields

- **`field`**: The business card field (uses `ExtractedField` enum)
- **`value`**: The extracted value
- **`message_id`**: ID of the message where this was extracted
- **`source`**: How it was extracted:
  - `"user_input"` - User explicitly provided this information
  - `"google_search"` - Extracted from Google search results
  - `"inference"` - Inferred from context
  - `"user_confirmation"` - User confirmed previously extracted value
- **`timestamp`**: UTC timestamp when extraction was recorded

### ExtractedField Enum

```python
class ExtractedField(str, Enum):
    BUSINESS_NAME = "name"
    WEBSITE = "website"
    SOCIAL_LINKS = "social_links"
    LOCATION = "location"
    SERVICE_TYPE = "service_type"
```

### Usage Patterns

#### Pattern 1: Check Before Asking

```python
# Before asking for location, check if we already have it:
if session_memory.has_extracted_field(ExtractedField.LOCATION):
    location = session_memory.get_extracted_field(ExtractedField.LOCATION)
    # Don't ask again - we already know it
else:
    # Ask the user for their location
    pass
```

#### Pattern 2: Record Extraction from Search

```python
# User provides website, agent searches and extracts info
session_memory.add_extraction(
    field=ExtractedField.WEBSITE,
    value="https://almacafe.co.il",
    message_id="msg_001",
    source="user_input"
)

session_memory.add_extraction(
    field=ExtractedField.BUSINESS_NAME,
    value="Alma Cafe",
    message_id="msg_001",
    source="google_search"
)
```

### Benefits

1. **Avoid Redundant Questions** - Check if field already extracted before asking
2. **Track Information Sources** - Audit trail of where each piece came from
3. **Message-Level Tracking** - Connect extractions to specific messages
4. **Timeline Awareness** - See chronological order of information gathering

---

## API Reference

### Workflow Stage API

#### Get Current Stage
```python
from workflow_enums import WorkflowStage

stage = session_memory.get_workflow_stage()
# Returns: WorkflowStage enum value or None
```

#### Set Stage (Orchestrator Only)
```python
# Using enum (recommended)
session_memory.set_workflow_stage(WorkflowStage.CAMPAIGN_BRIEF)

# Using string (also works - will be converted to enum)
session_memory.set_workflow_stage('campaign_brief')
```

### Shared State API

#### Business Card
```python
# Check if exists
has_bc = session_memory.has_business_card()

# Get business card
business_card = session_memory.get_business_card()

# Set business card
session_memory.set_business_card(business_card_data)
```

#### User Profile
```python
# Set user profile (authenticated users)
session_memory.set_user_profile({
    'name': 'John Doe'
})

# Get user profile
profile = session_memory.get_user_profile()
# Returns: {'name': 'John Doe'} or {} for anonymous
```

#### Messages
```python
# Add message to shared history
session_memory.add_message('user', 'Hello', message_id='msg_001')

# Access messages
messages = session_memory.shared_context['messages']
```

### Agent-Specific State API

#### Onboarding Extraction Memory

```python
from workflow_enums import ExtractedField, OnboardingStatus

# Initialize context
session_memory.initialize_onboarding_context()

# Record extraction
session_memory.add_extraction(
    field=ExtractedField.BUSINESS_NAME,
    value="Alma Cafe",
    message_id="msg_001",
    source="google_search"
)

# Check if field extracted
has_name = session_memory.has_extracted_field(ExtractedField.BUSINESS_NAME)

# Get extracted value
name = session_memory.get_extracted_field(ExtractedField.BUSINESS_NAME)

# Get full history
extractions = session_memory.get_extractions()

# Manage status
session_memory.set_onboarding_status(OnboardingStatus.AWAITING_CONFIRMATION)
status = session_memory.get_onboarding_status()
```

#### Generic Agent Context

```python
# Get agent-specific context
creator_context = session_memory.get_agent_context('creator_finder_agent')

# Update agent-specific context
session_memory.update_agent_context(
    'creator_finder_agent',
    'search_history',
    ['search_1', 'search_2']
)
```

---

## Summary

The Creo architecture provides:

- ✅ **Type safety** - Enums prevent typos and invalid values
- ✅ **Workflow coordination** - Stages prevent premature agent switching
- ✅ **State separation** - Clear boundaries between shared and agent-specific state
- ✅ **Extraction tracking** - Avoid redundant questions with memory
- ✅ **Scalability** - Easy to add new agents and workflow stages
- ✅ **Debuggability** - Clear logging of state changes and transitions
- ✅ **Testability** - Isolated agent state for independent testing

This architecture enables sophisticated multi-agent workflows while maintaining clean separation of concerns and preventing common coordination issues.
