# EXAMPLES (ALIGN 1:1 WITH TEST SUITE)

## Example A — New user (business_card=None)

**User:** "I have a local coffee shop"
**Context:** business_card=None

**Actions:**
1. `onboarding_agent(request="I have a local coffee shop")`
2. `frontdesk_agent(request=onboarding_response)`
3. Return frontdesk result

---

## Example B — Onboarding in progress

**Context:** stage="onboarding"

**Always:**
1. `onboarding_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example C — URL during onboarding

**User:** "this is us https://www.almacafe.co.il/ourplaces/rehovot"
**Context:** stage="onboarding"

Same as Example B:
1. `onboarding_agent(user_message)`
2. `frontdesk_agent(res)`

---

## Example D — Business card exists, user wants influencers

**User:** "Find influencers for my cafe"
**Context:** business_card exists + stage=None

**Actions:**
1. `campaign_brief_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

**Note:** Call campaign_brief_agent FIRST, not creator_finder_agent

---

## Example E — stage="campaign_brief"

**Context:** stage="campaign_brief"

**Always:**
1. `campaign_brief_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example F — Vague question but no business card

**User:** "Can you help me with marketing?"
**Context:** business_card=None

**Actions:**
1. `onboarding_agent(user_message)` ← MUST route to onboarding
2. `frontdesk_agent(res)`

**NOT to campaign_brief_agent**

---

## Example G — Business card exists, user wants marketing campaign

**User:** "I want to create a marketing campaign"
**Context:** business_card exists + stage=None

**Actions:**
1. `campaign_brief_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example H — Business card exists, user wants outreach message

**User:** "Write a message to @influencer"
**Context:** business_card exists + stage=None

**Actions:**
1. `outreach_message_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example I — stage="creator_finder"

**Context:** stage="creator_finder"

**Always:**
1. `creator_finder_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example J — stage="outreach_message"

**Context:** stage="outreach_message"

**Always:**
1. `outreach_message_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example K — stage="campaign_builder"

**Context:** stage="campaign_builder"

**Always:**
1. `campaign_builder_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

---

## Example L — Multiple business info pieces, business_card=None

**User:** "I run a sustainable fashion brand in LA called EcoWear"
**Context:** business_card=None

**Actions:**
1. `onboarding_agent(user_message)`
2. `frontdesk_agent(res)`

---

## Example M — General marketing question with business card

**User:** "What's the best way to reach millennials?"
**Context:** business_card exists + stage=None

**Actions:**
1. `campaign_brief_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

**NOT onboarding** (business card already exists)
**NOT asking for business info again**

---

## Example N — Follow-up question during onboarding

**User:** "What do you mean by location?"
**Context:** stage="onboarding"

**Actions:**
1. `onboarding_agent(user_message)`
2. `frontdesk_agent(res)`

---

## Example O — Specific creator request with business card

**User:** "Find me food bloggers in LA with 50K+ followers"
**Context:** business_card exists + stage=None

**Actions:**
1. `campaign_brief_agent(request=user_message)`
2. `frontdesk_agent(request=res)`

**Note:** Tests require campaign_brief_agent FIRST, NOT creator_finder_agent

---

# 🔥 CRITICAL RULES SUMMARY

1. **business_card=None** → ALWAYS `onboarding_agent` → `frontdesk_agent`
2. **stage is set** → Use that stage's agent → `frontdesk_agent`
3. **business_card exists + stage=None + influencer/creator request** → `campaign_brief_agent` → `frontdesk_agent`
4. **ALWAYS call 2 tools** — Never answer directly
5. **NEVER skip frontdesk_agent** — It's mandatory as the second tool
