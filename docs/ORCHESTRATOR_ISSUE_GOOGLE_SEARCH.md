# Critical Issue: Orchestrator Performing Actions Instead of Delegating

## The Problem

### What Happened
User provided: `"Alma cafe"`

Orchestrator responded: `"I'll go ahead and make sure I'm looking at the Alma Cafe in Rehovot, Israel."`

**HOW did it know about "Rehovot, Israel"?** The user never mentioned the location!

### Root Cause

The orchestrator (root_agent) has access to sub-agents wrapped as `AgentTool`, including `onboarding_agent` which has `GoogleSearchTool`. Instead of **delegating** to the onboarding agent, the orchestrator:

1. ❌ Searched Google directly for "Alma Cafe"
2. ❌ Found a real business "Alma Cafe in Rehovot, Israel"
3. ❌ Made an assumption this is the user's business
4. ❌ Skipped the onboarding workflow entirely

### Evidence from Logs

```
[SESSION_STATE] Session: session_accd... | Stage: None | Business Card: No
[SessionManager] Enhanced message with context:
  - Workflow stage: None
  - Business card: None
  - User message: Alma cafe...

[AGENT_TRANSITION] → root_agent | is_final: False
[AGENT_TRANSITION] → root_agent | is_final: False
[AGENT_TRANSITION] → root_agent | is_final: False
[AGENT_TRANSITION] → root_agent | is_final: True
```

**Notice:** ONLY `root_agent` appears! No `onboarding_agent`, no `frontdesk_agent`.

### What SHOULD Have Happened

```
[SESSION_STATE] Stage: None | Business Card: No

[AGENT_TRANSITION] → root_agent | is_final: False
  (Sees business_card: None, routes to onboarding_agent)

[AGENT_TRANSITION] → onboarding_agent | is_final: False
  (Asks user for business details, uses Google Search WITH user's permission)

[AGENT_TRANSITION] → frontdesk_agent | is_final: True
  (Formats response warmly)
```

## Why This Is Critical

### 1. **Privacy Violation**
- Searching for business information without user consent
- Making assumptions about which business the user owns
- Potentially exposing sensitive business data

### 2. **Wrong Assumptions**
- "Alma Cafe" could be:
  - A new business not yet on Google
  - A business with a common name (multiple "Alma Cafes" exist)
  - A planned business name
  - A different "Alma Cafe" than the one found
- **The system ASSUMED** it's the one in Rehovot, Israel

### 3. **Workflow Bypass**
- Onboarding agent has specific data collection logic
- Onboarding agent validates and confirms information
- Onboarding agent generates BUSINESS_CARD_CONFIRMATION
- **All of this was skipped!**

### 4. **No Data Persistence**
- Business card was never saved
- User will have to provide information again
- Session state not properly updated

## The Fix

### Updated Orchestrator Instructions

Added explicit rules to prevent the orchestrator from doing work:

```markdown
**CRITICAL: You are a ROUTER, not a DOER**
- You NEVER perform actions yourself (searching, collecting data, making assumptions)
- You ONLY analyze and delegate to specialized agents
- You NEVER use tools directly - only call sub-agents who use the tools
- You NEVER make assumptions about business details - let the onboarding agent gather information
```

### Mandatory Routing Rules

```markdown
**If business card is missing or None:**
- **IMMEDIATELY call `onboarding_agent`** - DO NOT ask questions yourself
- **DO NOT make assumptions** about business name, location, or any other details
- **DO NOT search** for business information yourself
- Let the onboarding agent handle ALL data collection
```

### Critical Rules Added

```markdown
7. **NEVER perform actions yourself - you are a ROUTER, not a DOER:**
   - ❌ DO NOT ask the user for business information yourself
   - ❌ DO NOT search Google for business details
   - ❌ DO NOT make assumptions about location, business type, etc.
   - ❌ DO NOT collect data directly from the user
   - ✅ ALWAYS delegate to the appropriate specialized agent
   - ✅ Let onboarding_agent handle ALL business data collection
```

## Expected Behavior After Fix

### Test Case 1: New User with Business Name

**User Input:** `"I have a coffee shop"`

**Expected Flow:**
```
1. Orchestrator sees: business_card: None
2. Orchestrator calls: onboarding_agent
3. Onboarding asks: "What's the name of your coffee shop?"
4. User replies: "Alma Cafe"
5. Onboarding asks: "Where is it located?"
6. User replies: "Brooklyn, NY"
7. Onboarding searches: google_search("Alma Cafe Brooklyn NY")
8. Onboarding confirms: "Is this your business at 123 Main St?"
9. User confirms: "Yes"
10. Onboarding generates: BUSINESS_CARD_CONFIRMATION
11. Frontdesk formats: Warm confirmation message
```

**Key Points:**
- ✅ Onboarding agent asks for location BEFORE searching
- ✅ User provides location explicitly
- ✅ Search uses user-provided location
- ✅ No assumptions made

### Test Case 2: User Provides Partial Info

**User Input:** `"Alma cafe"`

**WRONG Behavior (Before Fix):**
```
Orchestrator searches Google → Finds "Alma Cafe, Rehovot, Israel" → Assumes that's the business
```

**CORRECT Behavior (After Fix):**
```
1. Orchestrator sees: business_card: None
2. Orchestrator calls: onboarding_agent (IMMEDIATELY, no questions)
3. Onboarding responds: "Thanks! Where is Alma cafe located?"
4. User provides location
5. Onboarding confirms and saves
```

## How to Verify the Fix

### Step 1: Start New Session
Clear browser localStorage and start fresh session

### Step 2: Send Message
User: `"I have a local coffee shop"`

### Step 3: Check Logs
```
[SESSION_STATE] Stage: None | Business Card: No
[AGENT_TRANSITION] → root_agent
[AGENT_TRANSITION] → onboarding_agent ← MUST SEE THIS!
[AGENT_TRANSITION] → frontdesk_agent
```

### Step 4: Verify Response
Should ask for business information, NOT make assumptions:
- ✅ "What's the name of your coffee shop?"
- ✅ "Tell me about your business"
- ❌ "I found your business at [location]" (without asking for location first)

## Architectural Principle

**Separation of Concerns:**
- **Orchestrator (root_agent)**: Routes and coordinates workflows
- **Specialized Agents**: Perform actual work (search, collect, create)
- **Frontdesk Agent**: Formats responses for users

**The orchestrator should be "dumb" about domain work:**
- It knows WHICH agent to call
- It knows WHEN to call them
- It does NOT know HOW to do their work
- It does NOT have tools to do their work

## Testing Checklist

- [ ] New user provides business name → onboarding agent is called
- [ ] Onboarding agent asks for location BEFORE searching
- [ ] No Google searches happen without user-provided context
- [ ] Business card is saved with BUSINESS_CARD_CONFIRMATION
- [ ] Logs show proper agent transitions (root → onboarding → frontdesk)
- [ ] No assumptions made about business details
- [ ] Session state properly updated with workflow stage

## Related Files Modified

1. `/agents/orchestrator-agent/instruction.md`
   - Added "ROUTER, not a DOER" principle
   - Explicit rules against searching/collecting data
   - Mandatory delegation to onboarding when business_card is None

## Summary

The orchestrator was **overstepping its role** by:
1. Accessing tools (Google Search) that should only be used by specialized agents
2. Making assumptions about user data without proper collection workflow
3. Bypassing the onboarding process entirely

**The fix** enforces strict separation: orchestrator ONLY routes, specialized agents ONLY work.

This ensures:
- ✅ Proper data collection workflow
- ✅ User consent before searches
- ✅ No assumptions about business details
- ✅ Consistent user experience
- ✅ Privacy protection
