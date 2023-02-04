# README

Play conway's game of life in your browser, democratically electing the rules!

## Backend Spec

Game updates are computed on the server and pushed to the webpages using websockets. Input from each webpage comes back over the websocket.

Board states:

```json
{
    "type":"board",
    "board": {
        "roundNumber":3,
        "nextRoundTime":"2020-03-20T14:28:23.382748",
        "width": 2,
        "height": 2,
        "cells":[
            [{"playerId":"0118e439-8418-4004-91da-40c7f6db6c13"},{"playerId":"0118e439-8418-4004-91da-40c7f6db6c13"}],
            [{"playerId":"0118e439-8418-4004-91da-40c7f6db6c13"},{"playerId":"0118e439-8418-4004-91da-40c7f6db6c13"}]
        ]
    }
}
```

```json
{
    "type":"playerList",
    "players": {
        "0118e439-8418-4004-91da-40c7f6db6c13": {
            // TODO: Info about the player
        }
    }
}
```

```json
{
    "type":"yourPlayerInfo",
    "playerId":"0118e439-8418-4004-91da-40c7f6db6c13"
}
```

```json
{
    "type":"cooldownUpdate",
    "cooldownEndTime":"2020-03-20T14:28:23.382748"
}
```

Clicks & Other inputs from webpage:

```json
{
    "type":"addCell",
    "cellPosition": {
        "x":1,
        "y":0
    }
}
```

```json
{

}
```



---

Example board:
```json
{
	"board": {
		"roundNumber": 1,
		"width": 8,
		"height": 8,
		"cells": [
			[
				{
					"playerId": null
				},
				{
					"playerId": "1"
				},
				{
					"playerId": "0"
				},
				{
					"playerId": "2"
				},
				{
					"playerId": "0"
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				},
				{
					"playerId": null
				}
			],
			[
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": "2"
				},
				{
					"playerId": "2"
				},
				{
					"playerId": null
				},
				{
					"playerId": "1"
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				}
			],
			[
				{
					"playerId": "1"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": "2"
				},
				{
					"playerId": null
				},
				{
					"playerId": "1"
				}
			],
			[
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				}
			],
			[
				{
					"playerId": "2"
				},
				{
					"playerId": null
				},
				{
					"playerId": "1"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": "1"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				}
			],
			[
				{
					"playerId": "2"
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				},
				{
					"playerId": "0"
				},
				{
					"playerId": "0"
				},
				{
					"playerId": "1"
				},
				{
					"playerId": "1"
				},
				{
					"playerId": null
				}
			],
			[
				{
					"playerId": null
				},
				{
					"playerId": "2"
				},
				{
					"playerId": "1"
				},
				{
					"playerId": null
				},
				{
					"playerId": "0"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				}
			],
			[
				{
					"playerId": "0"
				},
				{
					"playerId": "2"
				},
				{
					"playerId": "0"
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				},
				{
					"playerId": null
				}
			]
		],
		"nextRoundTime": "2023-02-04T20:10:43.109896+00:00"
	},
	"type": "board"
}
```
