# Trainline

Method: email

- Tickets: sender `auto-confirm@info.thetrainline.com`, subjects
  `Vos billets...` / `Votre trajet a bien été modifié`.
- Promotions: sender `no-reply@comms.trainline`, ignore (noise).
- Gmail query: `from:auto-confirm@info.thetrainline.com "vos billets"` +
  date window.
- Pitfall: the "trajet modifié" email contains the MOST RECENT ticket, not
  the original one. Match against the correct transaction by amount.
- Result: 2/3 matched; one transaction had no identifiable PDF ticket.
