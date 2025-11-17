# Shared Context System - How All Agents Access Session Data

## Overview

All agents in the Creo system (orchestrator, onboarding, campaign-brief, etc.) have access to shared session context including:
- `workflow_state.stage` - Current workflow stage
- `business_card` - User's business information
- `onboarding_status` - Onboarding agent's internal status

## How It Works

### 1. SessionMemory Storage (server-side)

Located in `session_manager.py`, the `SessionMemory` class maintains:

```python
class SessionMemory:
    def __init__(self, session_id: str, user_id: str):
        self.shared_context = {
            'session_id': session_id,
            'user_id': user_id,
            'business_card': None,  # Shared across all agents
            'workflow_state': {
                'stage': None,  # WorkflowStage enum or None
            }
        }

        self.agent_contexts = {
            # Agent-specific memory (not shared)
            # 'onboarding_agent': {'status': OnboardingStatus.COLLECTING}
        }
```

### 2. Context Injection (message enhancement)

**CRITICAL:** Every user message is automatically enhanced with session context before being sent to the agent.

```python
def _build_message_with_context(session_id, user_message):
    """
    Prepends session context to EVERY user message.

    This ensures ALL agents see the context in conversation history.
    """
    return f"""
=== SESSION CONTEXT (accessible by all agents) ===
workflow_state.stage: 'onboarding'
business_card: None
onboarding_status: 'collecting'
=== END SESSION CONTEXT ===

User message: {user_message}
"""
```

**Example enhanced message:**
```
=== SESSION CONTEXT (accessible by all agents) ===
workflow_state.stage: None
business_card: None
=== END SESSION CONTEXT ===

User message: I wish to increase my brand awareness
```

### 3. How Agents Access Context

#### Orchestrator Agent (root_agent)
The orchestrator receives the enhanced message and uses it to route to appropriate agents:

```markdown
# In orchestrator instructions:

**Step 0: MANDATORY - Check workflow stage**
- Check `workflow_state.stage` in the session's shared context
- If stage is None and business_card is None:
  - Set stage to 'onboarding'
  - Call `onboarding_agent`
```

When the orchestrator calls `onboarding_agent` using `AgentTool`, the sub-agent receives the full conversation history, including the enhanced message with context.

#### Sub-Agents (onboarding, campaign-brief, etc.)

Sub-agents see the context in two ways:

1. **Direct access** - The enhanced message with context is in the conversation history
2. **Persistent across calls** - Since context is added to EVERY message, it's always visible

Example for campaign-brief-agent:
```markdown
# In campaign-brief instructions:

**BEFORE creating a campaign brief, verify business card exists:**

1. Check session context for business_card
2. If business_card is MISSING:
   - Return: "I need to know more about your business first"
   - Orchestrator will redirect to onboarding
```

### 4. Context Flow Example

**User sends:** "I want to find influencers"

**Step 1: Context Enhancement**
```python
# SessionManager enhances the message
enhanced_message = """
=== SESSION CONTEXT ===
workflow_state.stage: None
business_card: None
=== END SESSION CONTEXT ===

User message: I want to find influencers
"""
```

**Step 2: Orchestrator Receives Enhanced Message**
```
Orchestrator sees:
- workflow_state.stage: None
- business_card: None
- User wants to find influencers

Decision: Business card missing → route to onboarding_agent
```

**Step 3: Orchestrator Calls Onboarding Agent**
```python
# Orchestrator uses AgentTool to call onboarding_agent
# The sub-agent receives the conversation history, which includes
# the enhanced message with session context
```

**Step 4: Onboarding Agent Sees Context**
```
Onboarding agent receives conversation with:
=== SESSION CONTEXT ===
workflow_state.stage: None
business_card: None
=== END SESSION CONTEXT ===

[Previous conversation history]

Onboarding agent responds: "Let me learn about your business first..."
```

### 5. Context Updates

When agents update the shared context (e.g., onboarding saves business card), the next user message will include the updated context:

**Before onboarding:**
```
=== SESSION CONTEXT ===
business_card: None
```

**After onboarding:**
```
=== SESSION CONTEXT ===
business_card: {
  "business_name": "Alma Cafe",
  "location": "Brooklyn, NY",
  ...
}
```

## Key Architectural Points

### ✅ All Agents Have Access
- Context is prepended to EVERY user message
- Visible in conversation history
- Sub-agents called by orchestrator see the full history

### ✅ Single Source of Truth
- `SessionMemory` is the authoritative source
- Context is injected at message send time
- Always reflects current state

### ✅ Conversation History Preserves Context
- ADK maintains conversation history
- Each message includes context header
- Sub-agents see parent agent's context

### ❌ NOT Passed as Parameters
- We don't pass context as function arguments
- We don't use separate API calls for context
- Context is embedded in the message itself

## Logging for Observability

### Session State Logging
```
[SESSION_STATE] Session: session_abc123 | Stage: None | Business Card: No
```
Shows state BEFORE agent execution

### Agent Transition Logging
```
[AGENT_TRANSITION] → root_agent | Session: session_abc123 | is_final: False
[AGENT_TRANSITION] → onboarding_agent | Session: session_abc123 | is_final: False
[AGENT_TRANSITION] → frontdesk_agent | Session: session_abc123 | is_final: True
```
Shows which agents are being called

### Workflow State Logging
```
[WORKFLOW_STATE] After onboarding_agent: stage=campaign_brief
```
Shows state AFTER agent execution

### Context Enhancement Logging
```
[SessionManager] Enhanced message with context:
  - Workflow stage: None
  - Business card: None
  - User message: I wish to increase my brand awareness...
```
Shows what context is being sent

## Agent Responsibilities

### Orchestrator Agent
- **Read** workflow_state.stage from context
- **Decide** which agent to call based on stage and business_card
- **Route** to appropriate agent
- **Update** stage when agents complete

### Onboarding Agent
- **Read** business_card status from context
- **Collect** business information
- **Generate** BUSINESS_CARD_CONFIRMATION when complete
- Orchestrator detects confirmation and updates business_card in context

### Campaign Brief Agent
- **Read** business_card from context
- **Reject** if business_card is None
- **Create** personalized campaign brief using business_card data

### Other Agents
- All agents can read shared context
- Agents update context through special markers (BUSINESS_CARD_CONFIRMATION)
- Orchestrator handles context updates

## Common Issues and Solutions

### Issue: Agent doesn't see context
**Symptom:** Agent behaves as if business_card is None when it exists

**Solution:**
1. Check logs for `[SessionManager] Enhanced message with context`
2. Verify business_card is actually saved in SessionMemory
3. Ensure agent's instructions mention checking session context

### Issue: Context not updating
**Symptom:** business_card stays None after onboarding

**Solution:**
1. Check if onboarding agent generated BUSINESS_CARD_CONFIRMATION
2. Verify server.py parses and saves the business card
3. Check `[BUSINESS_CARD] Saved to storage` log

### Issue: Wrong agent called
**Symptom:** Orchestrator routes to wrong agent

**Solution:**
1. Check `[SESSION_STATE]` log shows correct stage
2. Verify orchestrator instructions match routing logic
3. Check if stage is being updated correctly

## Testing Context Sharing

### Test 1: Fresh Session (No Business Card)
```bash
# User message: "I want to find influencers"

# Expected logs:
[SESSION_STATE] Stage: None | Business Card: No
[SessionManager] Enhanced message with context:
  - Workflow stage: None
  - Business card: None
[AGENT_TRANSITION] → root_agent
[AGENT_TRANSITION] → onboarding_agent  # Should route here!
```

### Test 2: After Onboarding (Business Card Exists)
```bash
# User message: "I want to find influencers"

# Expected logs:
[SESSION_STATE] Stage: None | Business Card: Yes
[SessionManager] Enhanced message with context:
  - Workflow stage: None
  - Business card: {business_name: "Alma Cafe", ...}
[AGENT_TRANSITION] → root_agent
[AGENT_TRANSITION] → campaign_brief_agent  # Should route here!
```

## Summary

**The shared context system ensures ALL agents have access to session data by:**

1. **Storing** session data in `SessionMemory` (server-side)
2. **Injecting** context into EVERY user message
3. **Preserving** context in conversation history
4. **Making** context visible to orchestrator and all sub-agents
5. **Logging** context at every step for observability

**This architecture allows agents to make informed decisions based on:**
- What workflow stage we're in
- What data has been collected (business card)
- What the user is asking for

**Without context, agents would operate blindly and couldn't maintain workflow continuity.**
