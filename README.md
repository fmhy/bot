# fmhy/bot

This code is for FreeMediaBotYeah, a Discord bot made specifically for the FMHY Discord server. It provides numerous utilities and other tools to help keep the server running like a well-oiled machine.

**Note:** This source code is provided as-is for educational and development purposes only. You **shouldn't** self-host this. Support will not be provided if you choose to do so.

## Usage

1. You will need [`rye`](https://rye-up.com) to install dependencies and manage a virtualenv.
2. Install dependencies with `rye sync`.
3. Fill the config details in `.env`.
4. Run a production ready mongodb server, then start the bot with `rye run bot`.

## Development

1. [Follow the above](#usage)
2. Setup a development mongodb server. If you have node/bun, you can get upto speed with `[npx|pnpx|bunx] mongoz`, see [unjs/mongoz](https://github.com/unjs/mongoz).

## Contributing

1. Fork it (<https://github.com/fmhy/bot/fork>)
2. Create your feature branch (`git checkout -b my-new-feature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin my-new-feature`)
5. Create a new Pull Request

## Contributors

- [Terrence Tingleberry](https://github.com/maureenferreira)/@terrencetingleberry (Discord) - Creator & Original Programmer
- [rhld16](https://github.com/rhld16) - Wrangler of Code
- [taskylizard](https://github.com/taskylizard) - De-spaghettifier
- [Lix](https://github.com/daniel-lxs) - Morally Culpable
- jsmsj - Bookmarks Cog
