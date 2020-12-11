# ParrotBot
A Discord Bot which duplicates webhooks sent to channels into another channel based of keyword filtering.

## Prerequisites

- Python3
- Discord.py

## Getting Started

- Clone this repo
- Copy the `config.json` and the `relay_info.json` files from the templates folder into the same directory as the two Python files.
- Add your bots auth token to the `config.json` file, and if you wish to, change the prefix of the bot's commands.


## Commands

`>>parrot add` This command starts the process of adding a new channel link!
`>>parrot remove` This command starts the process of removing an existing channel link!
`>>parrot channels` This command displays all channel links, and the keywords which determin what is posted to them!
`>>parrot commands` This command displays a list of all available commands!