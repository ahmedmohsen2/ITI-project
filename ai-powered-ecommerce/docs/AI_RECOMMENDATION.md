# Recommendation design

The local recommendation engine requires no external AI service or API key. It ranks real active, in-stock products from the catalogue using recorded `UserInteraction` rows.

- **Personalized:** recent views, searches associated with a category, add-to-cart events, purchases, and recommendation clicks contribute weighted category affinity (weights 1, 1, 3, 5, and 2). The top category affinities surface unpurchased products in those categories. A new shopper receives a newest-items cold start with an honest discovery explanation.
- **Similar:** products in categories the customer viewed, excluding products already purchased or added to the bag.
- **Trending:** add-to-cart and purchase counts in the recent 30-day window; when history is sparse, view activity and newest products provide a deterministic fallback.
- **Explanations:** text refers only to the category and events that actually drove the rank. No invented personal attributes or generated behavior are used.

This is an explainable behavioral/content-ranking baseline, rather than a trained predictive model. A larger dataset could support offline evaluation and a learned ranking model later.
