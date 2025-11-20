# Examples

---

## Example 1 — URL provided → search → review block

User: "Yes, here is my website: https://www.almacafe.co.il/ourplaces/rehovot"

```
Extracted:
website raw = https://www.almacafe.co.il/ourplaces/rehovot
normalized = almacafe.co.il

google_search("site:almacafe.co.il") →
{
"name": "Alma Cafe",
"location": "Rehovot, Israel",
"service_type": "Coffee shop"
}
```

Output:
```
Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Website: almacafe.co.il
Social Links: Not provided

Does everything look correct?
```

---

## Example 2 — User confirms after review → save card

Context: Agent previously showed review block asking "Does everything look correct?"

User: "Yes that's correct!"

Output:
```
Business Name: Alma Cafe
Location: Rehovot, Israel
Service Type: Coffee shop
Website: almacafe.co.il
Social Links: Not provided

BUSINESS_CARD_CONFIRMATION:
{"name": "Alma Cafe", "location": "Rehovot, Israel", "service_type": "Coffee shop", "website": "almacafe.co.il", "social_links": "Not provided"}

Saving business card now.

save_business_card(
name="Alma Cafe",
location="Rehovot, Israel",
service_type="Coffee shop",
website="almacafe.co.il",
social_links="Not provided"
)
```

NOTE: This is Stage B - triggered after user confirms the Stage A review block. The agent has the extracted data in memory from the conversation flow, NOT from session_context.business_card.

---

## Example 3 — Name only → search fails → ask for location

User: "My business is called StyleHub"

```
Extracted: name = StyleHub

google_search("StyleHub") → insufficient info
```

Output:
```
What's your business location? (e.g., Austin, Texas, USA / London, UK / San Francisco, CA, USA)
```

---

## Example 4 — Handle with platform → search → full info → save

User: "Check out @designhub on Instagram"

```
Extracted: social = @designhub

google_search("@designhub instagram") →
{
"name": "DesignHub Studio",
"location": "New York, NY, USA",
"service_type": "Graphic Design"
}
```

Output:
```
Business Name: DesignHub Studio
Location: New York, NY, USA
Service Type: Graphic Design
Website: Not provided
Social Links: @designhub

BUSINESS_CARD_CONFIRMATION:
{"name": "DesignHub Studio", "location": "New York, NY, USA", "service_type": "Graphic Design", "website": "Not provided", "social_links": "@designhub"}

Saving business card now.

save_business_card(
name="DesignHub Studio",
location="New York, NY, USA",
service_type="Graphic Design",
website="Not provided",
social_links="@designhub"
)
```

---

## Example 5 — Full street address → normalize location

User: "We're at 123 Main Street, Suite 400, New York, NY 10001"

```
Extracted location raw = "123 Main Street, Suite 400, New York, NY 10001"
Normalized → "New York, NY"
```

Output:
```
What's your business name?
```

---

## Example 6 — Name + Location → search → ask for missing service_type

User: "I run TechStart in San Francisco"

```
Extracted:
name = TechStart
location = San Francisco

google_search("TechStart San Francisco") →
{
"name": "TechStart",
"location": "San Francisco, CA"
// service_type missing
}
```

Output:
```
What type of service does TechStart provide?
```

---

## Example 7 — All fields provided → search → confirm and save

User: "My business is EcoWear, we're a sustainable fashion brand in Portland, Oregon. Check us out at ecowear.com or @ecowear_official on Instagram"

```
Extracted:
name = EcoWear
location = Portland, Oregon → normalized to Portland, OR
service_type = sustainable fashion brand
website = ecowear.com
social_links = @ecowear_official

google_search("site:ecowear.com") →
{
"name": "EcoWear",
"location": "Portland, OR",
"service_type": "Sustainable Fashion"
}
```

Output:
```
Business Name: EcoWear
Location: Portland, OR
Service Type: Sustainable Fashion
Website: ecowear.com
Social Links: @ecowear_official

BUSINESS_CARD_CONFIRMATION:
{"name": "EcoWear", "location": "Portland, OR", "service_type": "Sustainable Fashion", "website": "ecowear.com", "social_links": "@ecowear_official"}

Saving business card now.

save_business_card(
name="EcoWear",
location="Portland, OR",
service_type="Sustainable Fashion",
website="ecowear.com",
social_links="@ecowear_official"
)
```

---

# END OF EXAMPLES
