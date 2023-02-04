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
        "cells":[
            [{"color":"#10bb10"},{"color":"#10bb10"}],
            [{"color":"#10bb10"},{"color":"#10bb10"}]
        ]
    }
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