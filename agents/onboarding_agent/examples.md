# ONBOARDING AGENT EXAMPLES

These examples align 1:1 with the test suite in `evaluation/test.json`.

---

## Example 1: User provides website URL

**User message:** "Yes, here is my website: https://www.almacafe.co.il/ourplaces/rehovot"

**Context:** business_card=null

**Agent response:**
```
Perfect! Let me look up your website to get the details...

[Uses google_search with the URL]

Great! I found information about your business. Let me confirm:

Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Website: https://www.almacafe.co.il/ourplaces/rehovot
Social Links: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "https://www.almacafe.co.il/ourplaces/rehovot",
  "social_links": "Not provided",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}
```

---

## Example 2: User provides business name and location

**User message:** "My business is called TechStart and we're located in San Francisco"

**Context:** business_card=null

**Agent response:**
```
Great! Let me search for TechStart in San Francisco to find more details about your business...

[Uses google_search("TechStart San Francisco")]

Perfect! I found your business. Let me confirm these details:

Business Name: TechStart
Location: San Francisco, CA
Service Type: Tech startup / SaaS
Website: https://www.techstart.com
Social Links: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "TechStart",
  "website": "https://www.techstart.com",
  "social_links": "Not provided",
  "location": "San Francisco, CA",
  "service_type": "Tech startup / SaaS"
}
```

---

## Example 3: Business card already exists

**User message:** "I want to find influencers for my brand"

**Context:** business_card exists (Alma Cafe)

**Agent response:**
```
Welcome back! I see we already have your details for Alma Cafe. Let's move forward with finding the perfect influencers for your coffee shop!
```

**Note:** NO google_search, NO BUSINESS_CARD_CONFIRMATION block needed

---

## Example 4: User confirms business details

**User message:** "Yes, that's correct!"

**Context:** business_card=null, last_agent_message contained business details

**Agent response:**
```
Perfect! Thanks for confirming those details for Alma Cafe. I've got everything I need.

Let's get started on finding the perfect influencers for your coffee shop!

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "https://www.almacafe.co.il/ourplaces/rehovot",
  "social_links": "Not provided",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}
```

---

## Example 5: New user with minimal info

**User message:** "I have a local coffee shop"

**Context:** business_card=null

**Agent response:**
```
That's wonderful! I'd love to help you with your coffee shop.

To give you the best recommendations, what's your shop's name and where are you located?
```

**Note:** Extracted service_type ("coffee shop"), but asking for name + location

---

## Example 6: User provides Instagram handle

**User message:** "My Instagram is @almacafe_rehovot"

**Context:** business_card=null

**Agent response:**
```
Great! Let me search for your business using your Instagram handle...

[Uses google_search("@almacafe_rehovot instagram")]

Perfect! I found your business information. Let me confirm:

Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Social Links: https://instagram.com/almacafe_rehovot
Website: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "Not provided",
  "social_links": "https://instagram.com/almacafe_rehovot",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}
```

---

## Example 7: Vague generic question (no context)

**User message:** "Can you help me with marketing?"

**Context:** business_card=null

**Agent response:**
```
Absolutely! I'd love to help you with your influencer marketing campaign.

To make sure I find the best match for you, could you tell me a bit about your business? What's your brand name and what industry are you in?
```

**Note:** NO google_search yet, asking for basic info first

---

## Example 8: User provides comprehensive info upfront

**User message:** "I run a sustainable fashion brand in LA called EcoWear"

**Context:** business_card=null

**Agent response:**
```
Awesome! A sustainable fashion brand - that's fantastic! Let me search for EcoWear in LA to find more details...

[Uses google_search("EcoWear sustainable fashion LA")]

Great! I found your brand. Let me confirm these details:

Business Name: EcoWear
Location: Los Angeles, CA
Service Type: Sustainable fashion brand
Website: https://www.ecowear.com
Social Links: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "EcoWear",
  "website": "https://www.ecowear.com",
  "social_links": "Not provided",
  "location": "Los Angeles, CA",
  "service_type": "Sustainable fashion brand"
}
```

**Note:** Extracted name, location, AND service_type from single message, then searched

---

## Example 9: User asks clarifying question

**User message:** "What do you mean by location?"

**Context:** business_card=null, last_agent_message asked for location

**Agent response:**
```
Great question! By location, I mean where your business operates. This could be:

- City and state (e.g., "Austin, Texas")
- City and country (e.g., "London, UK")
- A specific neighborhood (e.g., "Downtown Manhattan")
- Or if you serve customers online, you can say "Online" or "Nationwide"

Where is your business based?
```

**Note:** Provides helpful clarification with examples, remains patient

---

## Example 10: User provides business name only

**User message:** "My business is called StyleHub"

**Context:** business_card=null

**Agent response:**
```
Great! Let me search for StyleHub to find more information...

[Uses google_search("StyleHub")]

I found a few businesses with that name. To make sure I get the right one, could you tell me where StyleHub is located?
```

**Note:** Searches first, but if ambiguous results, asks for location to clarify

---

## Example 11: User provides TikTok handle

**User message:** "Check out our TikTok @ecowear_official"

**Context:** business_card=null

**Agent response:**
```
Perfect! Let me search for your business using your TikTok handle...

[Uses google_search("@ecowear_official tiktok")]

Great! I found your brand. Let me confirm:

Business Name: EcoWear
Location: Los Angeles, CA
Service Type: Sustainable fashion
Social Links: https://tiktok.com/@ecowear_official
Website: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "EcoWear",
  "website": "Not provided",
  "social_links": "https://tiktok.com/@ecowear_official",
  "location": "Los Angeles, CA",
  "service_type": "Sustainable fashion"
}
```

---

## Example 12: User corrects information during confirmation

**User message:** "No, the location is wrong - we're actually in San Jose, not San Francisco"

**Context:** business_card=null, last_agent_message showed incorrect location

**Agent response:**
```
Thanks for catching that! Let me update the location to San Jose:

Business Name: TechStart
Location: San Jose, CA
Service Type: Tech startup
Website: https://www.techstart.com
Social Links: Not provided

Does this look correct now?
```

**Note:** Acknowledges correction, updates info, asks for RE-confirmation. NO BUSINESS_CARD_CONFIRMATION block yet (waiting for user to confirm updated info)

---

## Example 13: User provides LinkedIn profile

**User message:** "Here's our LinkedIn: linkedin.com/company/techstart-inc"

**Context:** business_card=null

**Agent response:**
```
Great! Let me search for your business using your LinkedIn profile...

[Uses google_search("linkedin.com/company/techstart-inc")]

Perfect! I found your company details. Let me confirm:

Business Name: TechStart Inc
Location: San Francisco, CA
Service Type: B2B SaaS platform
Website: https://www.techstart.com
Social Links: https://linkedin.com/company/techstart-inc

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "TechStart Inc",
  "website": "https://www.techstart.com",
  "social_links": "https://linkedin.com/company/techstart-inc",
  "location": "San Francisco, CA",
  "service_type": "B2B SaaS platform"
}
```

---

## Example 14: User provides partial URL (no protocol)

**User message:** "Our site is almacafe.co.il"

**Context:** business_card=null

**Agent response:**
```
Perfect! Let me look up your website...

[Uses google_search("almacafe.co.il")]

Great! I found your cafe. Let me confirm these details:

Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Website: https://www.almacafe.co.il
Social Links: Not provided

Does everything look correct?

BUSINESS_CARD_CONFIRMATION:
{
  "name": "Alma Cafe",
  "website": "https://www.almacafe.co.il",
  "social_links": "Not provided",
  "location": "Rehovot, Israel",
  "service_type": "Coffee shop"
}
```

**Note:** Constructs full URL with https:// protocol

---

## Example 15: User gives full street address instead of city

**User message:** "We're at 123 Main Street, Suite 400, New York, NY 10001"

**Context:** business_card=null, last_agent_message asked for location

**Agent response:**
```
Perfect! I'll use New York, NY as your location.

[If enough info, searches and presents confirmation with location simplified to "New York, NY"]
```

**Note:** Extracts city/state, does NOT store full street address in business_card

---

# CRITICAL RULES SUMMARY

1. **If business_card exists** → Welcome back, confirm onboarding complete, NO search, NO BUSINESS_CARD_CONFIRMATION
2. **If URL/social/name+location provided** → ALWAYS google_search FIRST
3. **If comprehensive info in one message** → Extract all pieces, THEN search
4. **If vague question** → Ask for name + industry/service type conversationally
5. **If minimal info** → Extract what you can, ask for missing essentials
6. **When user confirms** → ALWAYS generate BUSINESS_CARD_CONFIRMATION block
7. **When user corrects** → Update info, re-present, ask for RE-confirmation (no block yet)
8. **When user clarifies** → Provide helpful explanation with examples, stay patient
