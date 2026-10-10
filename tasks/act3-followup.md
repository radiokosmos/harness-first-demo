Two steps, two separate queries:

1. Which customer email address appears in the most support tickets? Show the
   address and the count.
2. Then run a second query that filters `raw.support_tickets` on that exact
   address and lists ticket_id, channel and created_at. Say what they keep
   complaining about.
