# soshe chat
clone, run `python3 server.py`, and open `localhost:4242`

## features
- actually instant messaging - no signup needed
- link, image, and video embeds (youtube)
- active user counter
- typing indicators: "jim is typing..."
- instantly create a new room by just adding a uri,
  - ie: `localhost:4242/test` immediately creates and joins a room called test
- anonymized randomly generated usernames
- game commands
  - currently just `/tictactoe`

## planned
- instant group voice calling - just click a link and allow mic
- end to end encryption
  - all the necessary code is already clientside so this should be a breeze
- reply functionality
  - live threads, like reddit threads but live chat.
